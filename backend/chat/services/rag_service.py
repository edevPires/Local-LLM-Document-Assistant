"""
RAG Service — Retrieval-Augmented Generation com ChromaDB.

=== CONCEITO ===

RAG permite que o LLM responda com base no conteúdo dos documentos
enviados, em vez de depender apenas do conhecimento treino do modelo.

Fluxo:
    1. Upload de documento
        ↓
    2. document_service.extract_text()
        ↓
    3. rag_service.index_document()
        → Divide em chunks
        → Gera embeddings (sentence-transformers)
        → Salva no ChromaDB
        ↓
    4. User faz pergunta
        ↓
    5. rag_service.ask()
        → Embeda a pergunta
        → Busca chunks relevantes (similaridade semântica)
        → Monta prompt com contexto
        → Chama llm_service.chat()
        ↓
    6. Resposta contextualizada

=== BIBLIOTECAS ===

- chromadb: banco de dados vetorial persistente
- sentence-transformers: gera embeddings localmente (sem GPU necessária)

=== COLEÇÃO POR CONVERSA ===

Cada conversa tem sua própria coleção no ChromaDB: conversation_{id}
Isso isola os documentos de cada conversa e evita "vazamento" de contexto
entre conversas diferentes.
"""

import logging
from typing import Optional

import chromadb
from sentence_transformers import SentenceTransformer
from django.conf import settings

from . import llm_service

logger = logging.getLogger(__name__)

# Singleton — carregado uma única vez, reutilizado em todas as requisições
_client: Optional[chromadb.PersistentClient] = None
_model: Optional[SentenceTransformer] = None


def _get_client() -> chromadb.PersistentClient:
    """
    Inicializa o cliente ChromaDB com persistência em disco.
    Lazy initialization — só carrega quando necessário.
    """
    global _client
    if _client is None:
        logger.info("Inicializando ChromaDB em %s", settings.CHROMA_DB_PATH)
        _client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
    return _client


def _get_model() -> SentenceTransformer:
    """
    Carrega o modelo de embedding (all-MiniLM-L6-v2).
    ~90 MB, rodas na CPU. Lazy initialization.
    """
    global _model
    if _model is None:
        logger.info("Carregando modelo de embedding all-MiniLM-L6-v2")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def get_collection(conversation_id: int) -> chromadb.Collection:
    """
    Retorna ou cria a coleção ChromaDB para a conversa.

    CONCEITO: Cada conversa tem uma coleção separada para isolar
    documentos. A coleção é criada automaticamente se não existir.

    Args:
        conversation_id: ID da conversa

    Returns:
        chromadb.Collection para a conversa
    """
    client = _get_client()
    collection_name = f"conversation_{conversation_id}"

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}  # similaridade de cosseno
    )

    return collection


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """
    Divide um texto em chunks com overlap.

    CONCEITO: Um documento grande é dividido em pedaços menores.
    Overlap garante que a busca não perca contexto nas bordas.

    Exemplo:
        Texto: "ABCDEFGHIJ" (10 chars)
        chunk_size=5, overlap=2

        Chunk 1: "ABCDE"
        Chunk 2: "DEFGH"   (overlap: "DE")
        Chunk 3: "GHIJ"    (overlap: "GH")

    Args:
        text: texto completo
        chunk_size: tamanho de cada chunk (em caracteres)
        overlap: quantos caracteres do chunk anterior repetir

    Returns:
        lista de chunks
    """
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]

        if chunk.strip():  # ignora chunks vazios
            chunks.append(chunk.strip())

        start += chunk_size - overlap

    logger.info("Texto dividido em %d chunks (chunk_size=%d, overlap=%d)",
                len(chunks), chunk_size, overlap)
    return chunks


def index_document(document) -> None:
    """
    Indexa um documento: divide em chunks, gera embeddings, salva no ChromaDB.

    CONCEITO - FLUXO:
    1. Pega o texto já extraído do documento
    2. Divide em chunks
    3. Gera embeddings para cada chunk (sentence-transformers)
    4. Salva no ChromaDB com metadados
    5. Marca documento como is_indexed = True

    Args:
        document: instância de models.Document (deve ter extracted_text)

    Raises:
        ValueError: se o documento não tem texto extraído
    """
    if not document.extracted_text or not document.extracted_text.strip():
        raise ValueError("Documento não tem texto extraído (extracted_text vazio)")

    logger.info(
        "Indexando documento %d (%s) na conversa %d",
        document.id,
        document.original_filename,
        document.conversation_id,
    )

    # 1. Dividir em chunks
    chunks = _chunk_text(document.extracted_text, chunk_size=500, overlap=100)

    if not chunks:
        raise ValueError("Nenhum chunk foi gerado do documento")

    # 2. Gerar embeddings
    model = _get_model()
    # convert_to_numpy=True para ChromaDB aceitar (não quer tensores PyTorch)
    embeddings = model.encode(chunks, convert_to_numpy=True)

    # 3. Preparar IDs e metadados
    ids = [f"doc_{document.id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "document_id": str(document.id),
            "original_filename": document.original_filename,
            "chunk_index": str(i),
            "conversation_id": str(document.conversation_id),
        }
        for i in range(len(chunks))
    ]

    # 4. Salvar no ChromaDB
    collection = get_collection(document.conversation_id)
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )

    # 5. Marcar como indexado
    document.is_indexed = True
    document.save()

    logger.info(
        "Documento %d indexado com sucesso (%d chunks)",
        document.id,
        len(chunks),
    )


def search(
    conversation_id: int,
    query: str,
    n_results: int = 3,
) -> list[str]:
    """
    Busca semântica: retorna os chunks mais relevantes para a pergunta.

    CONCEITO: A pergunta é transformada em embedding usando o mesmo modelo.
    ChromaDB compara o embedding da pergunta com todos os embeddings dos chunks
    e retorna os mais similares (usando similaridade de cosseno).

    Args:
        conversation_id: ID da conversa (para acessar a coleção correta)
        query: pergunta do usuário
        n_results: quantos chunks retornar

    Returns:
        lista com os chunks mais relevantes (strings)
    """
    logger.info("Buscando chunks para: %s", query[:100])

    try:
        collection = get_collection(conversation_id)

        # Gerar embedding da pergunta
        model = _get_model()
        query_embedding = model.encode([query], convert_to_numpy=True)[0]

        # Buscar no ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, collection.count()),  # evita pedir mais que tem
        )

        if not results["documents"] or not results["documents"][0]:
            logger.warning("Nenhum chunk encontrado para: %s", query[:100])
            return []

        chunks = results["documents"][0]
        logger.info("Encontrados %d chunks", len(chunks))
        return chunks

    except Exception as e:
        logger.error("Erro ao buscar chunks: %s", e)
        return []


SYSTEM_PROMPT_RAG = """Você é um assistente especializado em análise de documentos.
Responda a pergunta usando APENAS os trechos fornecidos abaixo.
Se a resposta não estiver nos trechos, diga claramente que não encontrou a informação no documento.

=== TRECHOS DO DOCUMENTO ===
{context}

=== FIM DOS TRECHOS ===
Agora responda à pergunta do usuário com base nos trechos acima."""


def ask(
    conversation_id: int,
    question: str,
    history: list[dict],
) -> str:
    """
    Pipeline RAG completo: busca documentos, monta prompt, chama LLM.

    CONCEITO - FLUXO:
    1. search() → busca os 3 chunks mais relevantes
    2. Monta um novo prompt que inclui:
       - SYSTEM_PROMPT_RAG (instrução para usar os trechos)
       - trechos relevantes
       - histórico da conversa
    3. llm_service.chat() → chama o LLM com o novo prompt
    4. Retorna a resposta

    Args:
        conversation_id: ID da conversa
        question: pergunta do usuário
        history: histórico de mensagens (role + content)

    Returns:
        str: resposta gerada pelo LLM (contextualizada com os documentos)
    """
    logger.info("Iniciando pipeline RAG para conversa %d", conversation_id)

    # 1. Buscar chunks relevantes
    chunks = search(conversation_id, question, n_results=3)

    if not chunks:
        logger.warning(
            "Nenhum chunk encontrado. Caindo back para chat sem RAG."
        )
        return llm_service.chat(history)

    # 2. Montar contexto
    context = "\n\n".join(chunks)

    # 3. Preparar mensagens com o prompt RAG
    rag_system_prompt = SYSTEM_PROMPT_RAG.format(context=context)

    # Reconstruir histórico com o novo system prompt
    messages_with_rag = [{"role": "system", "content": rag_system_prompt}]

    # Adicionar histórico (excluindo qualquer system prompt anterior)
    for msg in history:
        if msg["role"] != "system":
            messages_with_rag.append(msg)

    # 4. Chamar o LLM
    logger.info("Chamando LLM com contexto RAG (%d chunks)", len(chunks))
    response = llm_service.chat(messages_with_rag)

    return response


def ask_stream(
    conversation_id: int,
    question: str,
    history: list[dict],
):
    """
    Pipeline RAG completo com streaming (generator).

    CONCEITO: Idêntico ao ask(), mas usa chat_stream() em vez de chat().
    Retorna um generator que yield tokens um a um.

    Args:
        conversation_id: ID da conversa
        question: pergunta do usuário
        history: histórico de mensagens

    Yields:
        str: tokens individuais da resposta (um a um)
    """
    logger.info("Iniciando pipeline RAG com streaming para conversa %d", conversation_id)

    # 1. Buscar chunks relevantes
    chunks = search(conversation_id, question, n_results=3)

    if not chunks:
        logger.warning(
            "Nenhum chunk encontrado. Caindo back para chat_stream sem RAG."
        )
        # Fallback: stream sem RAG
        yield from llm_service.chat_stream(history)
        return

    # 2. Montar contexto
    context = "\n\n".join(chunks)

    # 3. Preparar mensagens com o prompt RAG
    rag_system_prompt = SYSTEM_PROMPT_RAG.format(context=context)

    # Reconstruir histórico com o novo system prompt
    messages_with_rag = [{"role": "system", "content": rag_system_prompt}]

    # Adicionar histórico (excluindo qualquer system prompt anterior)
    for msg in history:
        if msg["role"] != "system":
            messages_with_rag.append(msg)

    # 4. Chamar o LLM com streaming
    logger.info("Chamando LLM com contexto RAG e streaming (%d chunks)", len(chunks))
    yield from llm_service.chat_stream(messages_with_rag)
