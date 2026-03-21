"use client";

import { useState, useEffect, useCallback } from "react";
import type { Conversation } from "@/types";
import { getConversations, createConversation, deleteConversation } from "@/lib/api";
import { Sidebar } from "@/components/Sidebar";
import { ChatArea } from "@/components/ChatArea";
import { FloatingInput } from "@/components/FloatingInput";
import { useChat } from "@/hooks/useChat";

export default function Home() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [isLoadingConvs, setIsLoadingConvs] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const {
    messages,
    isStreaming,
    streamingContent,
    isUploading,
    error,
    loadMessages,
    submit,
    setMessages,
  } = useChat(activeId);

  const fetchConversations = useCallback(async () => {
    try {
      const data = await getConversations();
      setConversations(data);
    } catch {
      // silencioso — backend pode estar offline
    } finally {
      setIsLoadingConvs(false);
    }
  }, []);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const handleSelect = useCallback(
    async (id: number) => {
      if (id === activeId) return;
      setActiveId(id);
      setMessages([]);
      setSidebarOpen(false);
      await loadMessages(id);
    },
    [activeId, loadMessages, setMessages]
  );

  const handleCreate = useCallback(async () => {
    try {
      const conv = await createConversation("Nova conversa");
      setConversations((prev) => [conv, ...prev]);
      setActiveId(conv.id);
      setMessages([]);
    } catch {
      // silencioso
    }
  }, [setMessages]);

  const handleDelete = useCallback(
    async (id: number) => {
      try {
        await deleteConversation(id);
        setConversations((prev) => prev.filter((c) => c.id !== id));
        if (activeId === id) {
          setActiveId(null);
          setMessages([]);
        }
      } catch {
        // silencioso
      }
    },
    [activeId, setMessages]
  );

  const handleSubmit = useCallback(
    async (text: string, file: File | null, thinking: boolean) => {
      await submit(text, file, thinking);
      setTimeout(() => fetchConversations(), 1500);
    },
    [submit, fetchConversations]
  );

  return (
    <div className="flex h-full bg-vscode-bg overflow-hidden">
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={handleSelect}
        onCreate={handleCreate}
        onDelete={handleDelete}
        isLoading={isLoadingConvs}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="flex-1 flex flex-col min-w-0">
        {/* Botão hamburger — só aparece no mobile */}
        <div className="flex items-center px-4 pt-3 pb-1 md:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="font-mono text-vscode-muted hover:text-white text-sm"
          >
            ☰
          </button>
        </div>
        <ChatArea
          messages={messages}
          isStreaming={isStreaming}
          streamingContent={streamingContent}
          conversationId={activeId}
        />

        {error && (
          <div className="shrink-0 mx-6 mb-2 px-3 py-2 bg-red-900/30 border border-red-700 text-xs text-red-300 font-mono">
            ✗ {error}
          </div>
        )}

        {activeId && (
          <FloatingInput
            onSubmit={handleSubmit}
            disabled={isStreaming || isUploading}
          />
        )}
      </main>
    </div>
  );
}
