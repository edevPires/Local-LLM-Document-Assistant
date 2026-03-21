"use client";

import { useEffect, useRef } from "react";
import type { Message } from "@/types";
import { MessageBubble } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";

interface Props {
  messages: Message[];
  isStreaming: boolean;
  streamingContent: string;
  conversationId: number | null;
}

export function ChatArea({ messages, isStreaming, streamingContent, conversationId }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming, streamingContent]);

  if (!conversationId) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-vscode-muted">
        <p className="text-4xl mb-4">⬡</p>
        <p className="font-mono text-sm">Selecione ou crie uma conversa</p>
      </div>
    );
  }

  if (messages.length === 0 && !isStreaming) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-vscode-muted">
        <p className="text-4xl mb-4">⬡</p>
        <p className="font-mono text-sm">Nenhuma mensagem ainda</p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-6 py-4">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {/* Bolha parcial durante streaming */}
      {isStreaming && streamingContent && (
        <MessageBubble
          message={{
            id: -1,
            conversation: conversationId,
            role: "assistant",
            content: streamingContent,
            created_at: new Date().toISOString(),
          }}
        />
      )}

      {/* Indicador de digitação (antes do primeiro token) */}
      {isStreaming && !streamingContent && <TypingIndicator />}

      <div ref={bottomRef} />
    </div>
  );
}
