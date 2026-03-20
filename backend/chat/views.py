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

    # 6. Gerar resumo via LLM
    try:
        summary = llm_service.summarize(extracted_text)
        document.summary = summary
        document.save()
        logger.info("Resumo gerado: %d caracteres", len(summary))
    except Exception as e:
        logger.error("Erro ao gerar resumo: %s", e)
        # Resumo é opcional — não deleta o documento se o LLM falhar
        document.summary = f"[Resumo não disponível: {str(e)}]"
        document.save()

    # 7. Indexar documento no ChromaDB (Milestone 3 — RAG)
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
