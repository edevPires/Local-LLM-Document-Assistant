"use client";

import { useRef, useCallback, useState } from "react";

interface Props {
  onSubmit: (text: string, file: File | null, thinking: boolean) => void;
  disabled?: boolean;
}

export function FloatingInput({ onSubmit, disabled = false }: Props) {
  const [text, setText] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [thinking, setThinking] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    const trimmed = text.trim();
    if ((!trimmed && !selectedFile) || disabled) return;
    onSubmit(trimmed, selectedFile, thinking);
    setText("");
    setSelectedFile(null);
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  }, [text, selectedFile, disabled, thinking, onSubmit]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;
      setSelectedFile(file);
      e.target.value = "";
    },
    []
  );

  return (
    <div className="shrink-0 bg-vscode-bg px-6 pb-5">
      {/* Arquivo em espera */}
      {selectedFile && (
        <div className="flex items-center gap-2 px-2 py-1 mb-1 text-xs text-vscode-muted font-mono">
          <span className="text-vscode-blue">📄</span>
          <span className="truncate">{selectedFile.name}</span>
          <button
            onClick={() => setSelectedFile(null)}
            className="ml-auto hover:text-vscode-text"
          >
            ✕
          </button>
        </div>
      )}

      <div className="bg-vscode-bg">
        {/* Linha superior */}
        <div className="h-px bg-vscode-border" />

        <div className="flex items-start px-3 py-3">
          {/* Seta prompt */}
          <span className="text-vscode-blue font-mono text-sm mt-[3px] mr-3 select-none shrink-0">
            {disabled ? <span className="animate-pulse">●</span> : "❯"}
          </span>

          {/* Textarea auto-resize */}
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              e.target.style.height = "auto";
              e.target.style.height = `${e.target.scrollHeight}px`;
            }}
            onKeyDown={handleKeyDown}
            placeholder={
              disabled
                ? "Aguardando resposta..."
                : "Mensagem  (Enter envia · Shift+Enter nova linha)"
            }
            rows={1}
            disabled={disabled}
            className="
              flex-1 resize-none bg-transparent text-vscode-text text-sm font-mono
              placeholder:text-vscode-muted/40 outline-none overflow-hidden
              disabled:opacity-40 min-h-[1.5rem] max-h-48
            "
          />

          {/* Botão de upload */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            title="Anexar PDF ou DOCX"
            className="ml-3 mt-[2px] text-vscode-muted hover:text-vscode-text disabled:opacity-30 text-sm shrink-0 transition-colors"
          >
            ⊕
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx"
            className="hidden"
            onChange={handleFileChange}
          />
        </div>

        {/* Linha inferior */}
        <div className="h-px bg-vscode-border" />

        {/* Toggle thinking — abaixo da linha */}
        <div className="px-3 pt-1.5">
          <button
            onClick={() => setThinking((v) => !v)}
            disabled={disabled}
            title={thinking ? "Thinking ON — desabilitar raciocínio" : "Thinking OFF — habilitar raciocínio"}
            className="text-[10px] font-mono transition-colors disabled:opacity-30"
            style={{ color: thinking ? "#3b78ff" : "#444" }}
            onMouseEnter={(e) => { if (!disabled) (e.currentTarget as HTMLButtonElement).style.color = thinking ? "#6699ff" : "#666"; }}
            onMouseLeave={(e) => { if (!disabled) (e.currentTarget as HTMLButtonElement).style.color = thinking ? "#3b78ff" : "#444"; }}
          >
            {thinking ? "[think:on]" : "[think:off]"}
          </button>
        </div>
      </div>
    </div>
  );
}
