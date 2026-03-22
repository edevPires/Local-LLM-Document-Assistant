"""
LLM Service — Integração com o llama-server via HTTP (API compatível com OpenAI).

=== ARQUITETURA ===

Em vez de carregar o modelo dentro do Django (llama-cpp-python), usamos o
llama-server como um processo separado. O Django faz chamadas HTTP para ele.

  llama-server (porta 8080)  ←→  llm_service.py  ←→  views.py
         ↕                                               ↕
      GPU / CUDA                                    API REST

=== COMO RODAR O SERVIDOR ===

  llama-server --model models/Qwen3-9B-Q4_K_M.gguf --n-gpu-layers -1 --ctx-size 32768 --port 8080
  (ou use o start-llama.bat na raiz do projeto)

=== API USADA ===

  POST http://127.0.0.1:8080/v1/chat/completions
  Body: {"messages": [...], "temperature": 0.7, "max_tokens": 2048}

  O llama-server segue a mesma interface da OpenAI, então funciona com
  qualquer cliente OpenAI-compatible.
"""

import json
import logging
import urllib.request
import urllib.error

from django.conf import settings

logger = logging.getLogger(__name__)

# ============================================================
# Prompt do sistema padrão
# ============================================================
SYSTEM_PROMPT = (
    "Você é um assistente de IA útil e amigável. "
    "Responda sempre em português brasileiro de forma clara e objetiva. "
    "Quando receber um documento para resumir, faça um resumo conciso "
    "destacando os pontos principais."
)


def _build_messages(messages_history):
    """Adiciona system prompt se não existir."""
    if not messages_history or messages_history[0]["role"] != "system":
        return [{"role": "system", "content": SYSTEM_PROMPT}] + messages_history
    return messages_history


def chat(messages_history, thinking: bool = False):
    """
    Envia mensagens ao LLM e retorna a resposta completa.

    Args:
        messages_history: lista de dicts com {"role": str, "content": str}
        thinking: se True, habilita o modo de raciocínio do Qwen3 (mais lento)

    Returns:
        str: a resposta gerada pelo modelo
    """
    messages = _build_messages(messages_history)

    payload_dict = {
        "messages": messages,
        "temperature": settings.LLM_TEMPERATURE,
        "max_tokens": settings.LLM_MAX_TOKENS,
        "stream": False,
    }
    if not thinking:
        payload_dict["chat_template_kwargs"] = {"enable_thinking": False}

    payload = json.dumps(payload_dict).encode("utf-8")

    req = urllib.request.Request(
        f"{settings.LLM_SERVER_URL}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    logger.info("Enviando %d mensagens ao llama-server...", len(messages))

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            response = data["choices"][0]["message"]["content"]
            logger.info("Resposta recebida (%d caracteres)", len(response))
            return response.strip()

    except urllib.error.URLError as e:
        logger.error("Erro ao conectar ao llama-server: %s", e)
        raise RuntimeError(
            "Não foi possível conectar ao llama-server. "
            "Certifique-se de que ele está rodando na porta 8080."
        ) from e


def chat_stream(messages_history, thinking: bool = False):
    """
    Envia mensagens ao LLM e retorna um generator que yield tokens um a um.

    Args:
        messages_history: lista de dicts com {"role": str, "content": str}
        thinking: se True, habilita o modo de raciocínio do Qwen3 (mais lento)

    Yield:
        str: cada token gerado pelo modelo
    """
    messages = _build_messages(messages_history)

    payload_dict = {
        "messages": messages,
        "temperature": settings.LLM_TEMPERATURE,
        "max_tokens": settings.LLM_MAX_TOKENS,
        "stream": True,
    }
    if not thinking:
        payload_dict["chat_template_kwargs"] = {"enable_thinking": False}

    payload = json.dumps(payload_dict).encode("utf-8")

    req = urllib.request.Request(
        f"{settings.LLM_SERVER_URL}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    logger.info("Iniciando streaming do llama-server...")

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue
                data_str = line[len("data:"):].strip()
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    delta = data["choices"][0].get("delta", {})
                    token = delta.get("content", "")
                    if token:
                        yield token
                except (json.JSONDecodeError, KeyError):
                    continue

    except urllib.error.URLError as e:
        logger.error("Erro ao conectar ao llama-server: %s", e)
        raise RuntimeError(
            "Não foi possível conectar ao llama-server. "
            "Certifique-se de que ele está rodando na porta 8080."
        ) from e


def summarize(text, max_chunk_size=3000):
    """
    Gera um resumo de um texto (extraído de um documento).

    Estratégia: se cabe no contexto, resume direto.
    Se não, divide em chunks, resume cada um, e combina.

    Args:
        text: texto extraído do documento
        max_chunk_size: tamanho máximo em caracteres por chunk

    Returns:
        str: resumo do documento
    """
    if len(text) <= max_chunk_size:
        return chat([{
            "role": "user",
            "content": (
                "Faça um resumo conciso e bem estruturado do seguinte documento. "
                "Destaque os pontos principais, conclusões e informações relevantes:\n\n"
                f"{text}"
            ),
        }])

    # Texto grande → divide em chunks
    logger.info("Documento grande (%d chars), dividindo em chunks...", len(text))
    chunks = [text[i:i + max_chunk_size] for i in range(0, len(text), max_chunk_size)]
    partial_summaries = []

    for i, chunk in enumerate(chunks):
        logger.info("Resumindo chunk %d/%d...", i + 1, len(chunks))
        summary = chat([{
            "role": "user",
            "content": (
                f"Resuma a seguinte parte de um documento (parte {i + 1} de {len(chunks)}):\n\n"
                f"{chunk}"
            ),
        }])
        partial_summaries.append(summary)

    combined = "\n\n".join(partial_summaries)
    logger.info("Combinando %d resumos parciais...", len(partial_summaries))

    return chat([{
        "role": "user",
        "content": (
            "Os seguintes são resumos parciais de diferentes partes de um documento. "
            "Combine-os em um resumo final coeso e bem estruturado:\n\n"
            f"{combined}"
        ),
    }])
