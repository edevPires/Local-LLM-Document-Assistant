"use client";

import { useState, useCallback, useRef } from "react";
import type { Message, Document } from "@/types";
import { getMessages, sendMessageStream, uploadDocument } from "@/lib/api";

// IDs temporários negativos para não colidir com IDs reais do backend
let tempIdCounter = -1;
const nextTempId = () => tempIdCounter--;

export function useChat(conversationId: number | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const accumulatedRef = useRef("");

  const loadMessages = useCallback(async (convId: number) => {
    try {
      const msgs = await getMessages(convId);
      setMessages(msgs);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar mensagens");
    }
  }, []);

  const sendMessage = useCallback(
    async (content: string, displayContent?: string, thinking = false) => {
      if (!conversationId || isStreaming) return;

      setError(null);
      setIsStreaming(true);
      setStreamingContent("");
      accumulatedRef.current = "";

      const tempUserMsg: Message = {
        id: nextTempId(),
        conversation: conversationId,
        role: "user",
        content: displayContent ?? content,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, tempUserMsg]);

      try {
        await sendMessageStream(
          conversationId,
          content,
          thinking,
          (token) => {
            accumulatedRef.current += token;
            setStreamingContent(accumulatedRef.current);
          },
          (messageId) => {
            const finalContent = accumulatedRef.current;
            setMessages((prev) => [
              ...prev,
              {
                id: messageId,
                conversation: conversationId,
                role: "assistant",
                content: finalContent,
                created_at: new Date().toISOString(),
              },
            ]);
            setStreamingContent("");
            setIsStreaming(false);
            accumulatedRef.current = "";
          },
          (errMsg) => {
            setError(errMsg);
            setIsStreaming(false);
            setStreamingContent("");
            accumulatedRef.current = "";
          }
        );
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erro desconhecido");
        setIsStreaming(false);
        setStreamingContent("");
        accumulatedRef.current = "";
      }
    },
    [conversationId, isStreaming]
  );

  const uploadFile = useCallback(
    async (file: File): Promise<void> => {
      if (!conversationId) return;
      setIsUploading(true);
      setError(null);
      try {
        const doc = await uploadDocument(conversationId, file);
        setDocuments((prev) => [...prev, doc]);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erro ao enviar arquivo");
        throw e;
      } finally {
        setIsUploading(false);
      }
    },
    [conversationId]
  );

  /**
   * Fluxo correto:
   * 1. Mostra bolha do usuário imediatamente (com nome do arquivo se houver)
   * 2. Faz upload + indexação (sem inserir mensagem extra)
   * 3. Envia texto ao LLM (que já encontra o doc indexado via RAG)
   */
  const submit = useCallback(
    async (content: string, file: File | null, thinking = false) => {
      if (!conversationId) return;

      const displayContent = file
        ? content ? `📎 ${file.name}\n\n${content}` : `📎 ${file.name}`
        : content;

      // 1. Bolha do usuário aparece imediatamente
      const tempUserMsg: Message = {
        id: nextTempId(),
        conversation: conversationId,
        role: "user",
        content: displayContent,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, tempUserMsg]);

      // 2. Upload silencioso (sem mensagem de confirmação)
      if (file) {
        setIsUploading(true);
        setError(null);
        try {
          const doc = await uploadDocument(conversationId, file);
          setDocuments((prev) => [...prev, doc]);
        } catch (e) {
          setError(e instanceof Error ? e.message : "Erro ao enviar arquivo");
          setIsUploading(false);
          return;
        }
        setIsUploading(false);
      }

      // 3. Envia ao LLM — inclui o nome do arquivo quando enviado junto com pergunta
      // Isso dá sinal semântico para o RAG buscar chunks do documento correto
      const llmContent = file && content.trim()
        ? `[Documento: ${file.name}]\n\n${content}`
        : content;

      if (llmContent.trim()) {
        setError(null);
        setIsStreaming(true);
        setStreamingContent("");
        accumulatedRef.current = "";

        try {
          await sendMessageStream(
            conversationId,
            llmContent,
            thinking,
            (token) => {
              accumulatedRef.current += token;
              setStreamingContent(accumulatedRef.current);
            },
            (messageId) => {
              const finalContent = accumulatedRef.current;
              setMessages((prev) => [
                ...prev,
                {
                  id: messageId,
                  conversation: conversationId,
                  role: "assistant",
                  content: finalContent,
                  created_at: new Date().toISOString(),
                },
              ]);
              setStreamingContent("");
              setIsStreaming(false);
              accumulatedRef.current = "";
            },
            (errMsg) => {
              setError(errMsg);
              setIsStreaming(false);
              setStreamingContent("");
              accumulatedRef.current = "";
            }
          );
        } catch (e) {
          setError(e instanceof Error ? e.message : "Erro desconhecido");
          setIsStreaming(false);
          setStreamingContent("");
          accumulatedRef.current = "";
        }
      }
    },
    [conversationId]
  );

  return {
    messages,
    isStreaming,
    streamingContent,
    documents,
    isUploading,
    error,
    loadMessages,
    sendMessage,
    uploadFile,
    submit,
    setMessages,
  };
}
