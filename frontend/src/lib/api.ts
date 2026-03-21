import type { Conversation, Message, Document } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Conversations ──────────────────────────────────────────────────────────

export async function getConversations(): Promise<Conversation[]> {
  const res = await fetch(`${API_URL}/api/conversations/`);
  if (!res.ok) throw new Error("Erro ao buscar conversas");
  return res.json();
}

export async function createConversation(title = "Nova conversa"): Promise<Conversation> {
  const res = await fetch(`${API_URL}/api/conversations/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("Erro ao criar conversa");
  return res.json();
}

// ── Messages ───────────────────────────────────────────────────────────────

export async function deleteConversation(conversationId: number): Promise<void> {
  const res = await fetch(`${API_URL}/api/conversations/${conversationId}/`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Erro ao deletar conversa");
}

export async function getMessages(conversationId: number): Promise<Message[]> {
  const res = await fetch(`${API_URL}/api/conversations/${conversationId}/messages/`);
  if (!res.ok) throw new Error("Erro ao buscar mensagens");
  return res.json();
}

export async function sendMessageStream(
  conversationId: number,
  content: string,
  thinking: boolean,
  onToken: (token: string) => void,
  onDone: (messageId: number, userMessageId: number) => void,
  onError: (error: string) => void
): Promise<void> {
  const res = await fetch(
    `${API_URL}/api/conversations/${conversationId}/messages/stream/`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content, thinking }),
    }
  );

  if (!res.ok || !res.body) {
    onError("Falha na conexão com o servidor");
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    // Manter a última linha incompleta no buffer
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const raw = line.slice(6).trim();
      if (!raw) continue;

      try {
        const data = JSON.parse(raw);
        if (data.token !== undefined) {
          onToken(data.token);
        } else if (data.done) {
          onDone(data.message_id, data.user_message_id);
        } else if (data.error) {
          onError(data.error);
        }
      } catch {
        // linha SSE mal formada — ignorar
      }
    }
  }
}

// ── Documents ──────────────────────────────────────────────────────────────

export async function uploadDocument(
  conversationId: number,
  file: File
): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(
    `${API_URL}/api/conversations/${conversationId}/documents/`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error ?? "Erro ao enviar arquivo");
  }
  return res.json();
}
