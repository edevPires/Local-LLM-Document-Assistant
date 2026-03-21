"""
Views — Endpoints da API REST.

=== CONCEITO ===

No Django REST Framework, uma VIEW é uma função ou classe que:
1. Recebe uma request HTTP (GET, POST, DELETE, etc.)
2. Processa a lógica de negócio
3. Retorna uma response HTTP (geralmente JSON)

Usamos dois tipos aqui:

1. ModelViewSet:
   Gera automaticamente CRUD completo (list, create, retrieve, destroy)
   para um modelo. É o atalho mais poderoso do DRF.

2. @api_view:
   Decorator para funções simples. Usado quando o ViewSet
   padrão não cobre a lógica que precisamos (como enviar mensagem ao LLM).

=== FLUXO DE UMA REQUEST ===

Frontend POST /api/conversations/1/messages/ {"content": "Olá"}
  → Django URL router encontra a view correspondente
  → View valida os dados com o Serializer
  → View chama o llm_service para gerar resposta
  → View salva a mensagem do usuário e do assistente no banco
  → View retorna o JSON com a resposta
"""

import logging
import json

from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Conversation, Message, Document
from .serializers import ConversationSerializer, MessageSerializer, DocumentSerializer

from .services import llm_service, document_service, rag_service

logger = logging.getLogger(__name__)


class ConversationViewSet(viewsets.ModelViewSet):
    """
    CRUD completo de Conversas.

    CONCEITO: O ModelViewSet gera automaticamente:
      GET    /api/conversations/      → list()     → lista todas
      POST   /api/conversations/      → create()   → cria uma nova
      GET    /api/conversations/{id}/ → retrieve() → detalhe de uma
      PUT    /api/conversations/{id}/ → update()   → atualiza
      DELETE /api/conversations/{id}/ → destroy()  → deleta

    Você não precisa escrever nenhuma dessas funções manualmente!
    O DRF gera tudo baseado no queryset e serializer_class.
    """

    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer


@api_view(["GET"])
def list_messages(request, conversation_id):
    """
    GET /api/conversations/{id}/messages/
    Retorna todas as mensagens de uma conversa.

    CONCEITO: Usamos filter() para buscar apenas as mensagens
    da conversa especificada. O Django ORM traduz isso em:
    SELECT * FROM chat_message WHERE conversation_id = ?
    """
    try:
        conversation = Conversation.objects.get(pk=conversation_id)
    except Conversation.DoesNotExist:
        return Response(
            {"error": "Conversa não encontrada"},
            status=status.HTTP_404_NOT_FOUND,
        )

    messages = conversation.messages.all()
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def send_message(request, conversation_id):
    """
    POST /api/conversations/{id}/messages/
    Envia uma mensagem do usuário e retorna a resposta do LLM.

    CONCEITO - FLUXO COMPLETO:
    1. Recebe {"content": "Olá, como vai?"} do frontend
    2. Salva a mensagem do usuário no banco
    3. Busca todo o histórico da conversa
    4. Monta a lista de mensagens para o LLM
    5. Chama llm_service.chat() que:
       a. Formata em ChatML
       b. Envia ao modelo Qwen na GPU
       c. Retorna a resposta gerada
    6. Salva a resposta do assistente no banco
    7. Retorna ambas as mensagens ao frontend
    """
    # 1. Validar que a conversa existe
    try:
        conversation = Conversation.objects.get(pk=conversation_id)
    except Conversation.DoesNotExist:
        return Response(
            {"error": "Conversa não encontrada"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # 2. Validar o conteúdo da mensagem
    content = request.data.get("content", "").strip()
    if not content:
        return Response(
            {"error": "O campo 'content' é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 3. Salvar a mensagem do usuário no banco
    user_message = Message.objects.create(
        conversation=conversation,
        role="user",
        content=content,
    )

    # 4. Buscar histórico completo da conversa para dar contexto ao LLM
    history = conversation.messages.all().values("role", "content")
    messages_for_llm = [{"role": m["role"], "content": m["content"]} for m in history]

    # 5. Chamar o LLM (com ou sem RAG)
    try:
        # Verificar se a conversa tem documentos indexados (Milestone 3)
        has_rag = conversation.documents.filter(is_indexed=True).exists()
        if has_rag:
            logger.info("Usando RAG para responder (conversa %d tem documentos indexados)", conversation_id)
            assistant_response = rag_service.ask(conversation_id, content, messages_for_llm)
        else:
            logger.info("Chat sem RAG (conversa %d não tem documentos indexados)", conversation_id)
            assistant_response = llm_service.chat(messages_for_llm)
    except Exception as e:
        logger.error("Erro ao chamar o LLM: %s", e)
        assistant_response = f"Erro ao gerar resposta: {str(e)}"

    # 6. Salvar a resposta do assistente no banco
    assistant_message = Message.objects.create(
        conversation=conversation,
        role="assistant",
        content=assistant_response,
    )

    # 7. Atualizar o título da conversa se for a primeira mensagem
    if conversation.messages.count() == 2:  # user + assistant
        # Usa as primeiras palavras da mensagem como título
        title = content[:50] + ("..." if len(content) > 50 else "")
        conversation.title = title
        conversation.save()

    # 8. Retornar ambas as mensagens
    return Response(
        {
            "user_message": MessageSerializer(user_message).data,
            "assistant_message": MessageSerializer(assistant_message).data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
def upload_document(request, conversation_id):
    """
    POST /api/conversations/{id}/documents/
    Faz upload de um PDF ou DOCX, extrai o texto e gera um resumo via LLM.

    CONCEITO - FLUXO COMPLETO:
    1. Recebe o arquivo via multipart/form-data
    2. Salva o arquivo no disco (backend/media/documents/)
    3. document_service extrai o texto puro do arquivo
    4. llm_service.summarize() gera um resumo do texto
    5. Salva tudo no modelo Document
    6. Retorna o documento com o resumo gerado
    """
    # 1. Validar que a conversa existe
    try:
        conversation = Conversation.objects.get(pk=conversation_id)
    except Conversation.DoesNotExist:
        return Response(
            {"error": "Conversa não encontrada"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # 2. Validar que um arquivo foi enviado
    file = request.FILES.get("file")
    if not file:
        return Response(
            {"error": "Nenhum arquivo enviado. Use o campo 'file'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 3. Validar extensão
    allowed = (".pdf", ".docx", ".doc")
    ext = "." + file.name.rsplit(".", 1)[-1].lower() if "." in file.name else ""
    if ext not in allowed:
        return Response(
            {"error": f"Formato não suportado: '{ext}'. Use PDF ou DOCX."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 4. Salvar o documento no banco (arquivo vai para media/documents/)
    document = Document.objects.create(
        conversation=conversation,
        file=file,
        original_filename=file.name,
    )

    # 5. Extrair texto do arquivo salvo no disco
    try:
        extracted_text = document_service.extract_text(document.file.path)
        document.extracted_text = extracted_text
        document.save()
        logger.info("Texto extraído: %d caracteres", len(extracted_text))
    except Exception as e:
        document.delete()
        logger.error("Erro ao extrair texto: %s", e)
        return Response(
            {"error": f"Erro ao extrair texto: {str(e)}"},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # 6. Indexar documento no ChromaDB (Milestone 3 — RAG)
    # Resumo automático removido: a IA não deve tomar decisões sem o usuário pedir.
    try:
        rag_service.index_document(document)
        logger.info("Documento %d indexado com sucesso no ChromaDB", document.id)
    except Exception as e:
        logger.error("Erro ao indexar documento no ChromaDB: %s", e)
        # Indexação falha silenciosamente — documento ainda é útil sem RAG

    return Response(
        DocumentSerializer(document).data,
        status=status.HTTP_201_CREATED,
    )


@csrf_exempt
def send_message_stream(request, conversation_id):
    """
    POST /api/conversations/{id}/messages/stream/
    Envia mensagem e retorna resposta via SSE (Server-Sent Events).

    CONCEITO - FLUXO COMPLETO:
    1. Recebe {"content": "Olá, como vai?"} do frontend
    2. Salva a mensagem do usuário no banco
    3. Busca todo o histórico da conversa
    4. Monta a lista de mensagens para o LLM
    5. Chama llm_service.chat_stream() ou rag_service.ask_stream()
    6. Faz yield de cada token como evento SSE
    7. Ao terminar, salva a mensagem do assistente no banco
    8. Retorna resposta com `done: true`

    Formato SSE:
        data: {"token": "O"}
        data: {"token": " contrato"}
        data: {"done": true, "message_id": 42}
    """
    # 1. Validar que a conversa existe
    try:
        conversation = Conversation.objects.get(pk=conversation_id)
    except Conversation.DoesNotExist:
        return Response(
            {"error": "Conversa não encontrada"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # 2. Validar o conteúdo da mensagem
    try:
        data = json.loads(request.body.decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return StreamingHttpResponse(
            "data: " + json.dumps({"error": "Corpo JSON inválido"}) + "\n\n",
            content_type="text/event-stream",
            status=400
        )

    content = data.get("content", "").strip()
    if not content:
        return StreamingHttpResponse(
            "data: " + json.dumps({"error": "O campo 'content' é obrigatório"}) + "\n\n",
            content_type="text/event-stream",
            status=400
        )

    thinking = bool(data.get("thinking", False))

    # 3. Salvar a mensagem do usuário no banco ANTES de fazer streaming
    user_message = Message.objects.create(
        conversation=conversation,
        role="user",
        content=content,
    )

    # 4. Buscar histórico completo da conversa para dar contexto ao LLM
    history = list(conversation.messages.all().values("role", "content"))
    messages_for_llm = [{"role": m["role"], "content": m["content"]} for m in history]

    # 5. Detectar se usa RAG ou chat simples
    has_rag = conversation.documents.filter(is_indexed=True).exists()

    def event_stream():
        """Generator SSE: yield cada token como evento JSON."""
        full_response = []
        assistant_message = None

        try:
            logger.info("Iniciando stream para conversa %d (RAG=%s)", conversation_id, has_rag)

            # Escolher gerador (RAG ou chat simples)
            if has_rag:
                logger.info("Usando RAG para stream (thinking=%s)", thinking)
                token_gen = rag_service.ask_stream(conversation_id, content, messages_for_llm, thinking=thinking)
            else:
                logger.info("Chat stream sem RAG (thinking=%s)", thinking)
                token_gen = llm_service.chat_stream(messages_for_llm, thinking=thinking)

            # Iterar tokens e fazer yield como SSE
            for token in token_gen:
                full_response.append(token)
                payload = json.dumps({"token": token}, ensure_ascii=False)
                yield f"data: {payload}\n\n"

            logger.info("Tokens recebidos: %d", len(full_response))

        except Exception as e:
            logger.error("Erro no streaming: %s", str(e), exc_info=True)
            error_payload = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"data: {error_payload}\n\n"

        finally:
            # Salvar resposta do assistente
            assistant_text = "".join(full_response) if full_response else "[Resposta vazia]"

            try:
                assistant_message = Message.objects.create(
                    conversation=conversation,
                    role="assistant",
                    content=assistant_text,
                )

                # Atualizar título se primeira resposta
                if conversation.messages.count() == 2:
                    title = content[:50] + ("..." if len(content) > 50 else "")
                    conversation.title = title
                    conversation.save()

                logger.info("Resposta salva: message_id=%d", assistant_message.id)

            except Exception as e:
                logger.error("Erro ao salvar resposta: %s", str(e), exc_info=True)

            # Enviar evento final
            if assistant_message:
                done_payload = json.dumps(
                    {
                        "done": True,
                        "message_id": assistant_message.id,
                        "user_message_id": user_message.id,
                    },
                    ensure_ascii=False,
                )
                yield f"data: {done_payload}\n\n"

    # Retornar resposta com tipo SSE
    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
