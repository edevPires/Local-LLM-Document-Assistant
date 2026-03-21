"use client";

import type { Conversation } from "@/types";

interface Props {
  conversations: Conversation[];
  activeId: number | null;
  onSelect: (id: number) => void;
  onCreate: () => void;
  isLoading?: boolean;
  isOpen?: boolean;
  onClose?: () => void;
  onDelete?: (id: number) => void;
}

export function Sidebar({ conversations, activeId, onSelect, onCreate, isLoading, isOpen = true, onClose, onDelete }: Props) {
  return (
    <>
      {/* Backdrop mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/60 md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed inset-y-0 left-0 z-30 w-60 flex flex-col h-full
          transition-transform duration-200
          md:relative md:translate-x-0 md:z-auto
          ${isOpen ? "translate-x-0" : "-translate-x-full"}
        `}
        style={{ background: "#0f0f0f", borderRight: "1px solid #222" }}
      >

      {/* Branding */}
      <div className="px-4 pt-4 pb-3">
        <pre className="font-mono leading-[1.2] select-none overflow-hidden" style={{ fontSize: "7px", color: "#ffffff", opacity: 0.9 }}>{[
` ____  _____ ____  _   _ __  __ _____`,
`|  _ \\| ____/ ___|| | | |  \\/  | ____|`,
`| |_) |  _| \\___ \\| | | | |\\/| |  _|  `,
`|  _ <| |___ ___) | |_| | |  | | |___`,
`|_| \\_\\_____|____/ \\___/|_|  |_|_____|`,
`    _    ___`,
`   / \\  |_ _|`,
`  / _ \\  | |`,
` / ___ \\ | |`,
`/_/   \\_\\___|`,
].join("\n")}</pre>
      </div>

      {/* Botão nova conversa — TOPO */}
      <div className="px-4 pb-4">
        <button
          onClick={onCreate}
          className="
            w-full py-2 text-xs font-mono
            transition-colors duration-150
            flex items-center justify-center gap-2
          "
          style={{ color: "#555", border: "2px solid #333" }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.color = "#3b78ff";
            (e.currentTarget as HTMLButtonElement).style.borderColor = "#3b78ff";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.color = "#555";
            (e.currentTarget as HTMLButtonElement).style.borderColor = "#2a2a2a";
          }}
        >
          <span>+</span>
          <span>nova conversa</span>
        </button>
      </div>

      <div className="h-px mx-4" style={{ background: "#1e1e1e" }} />

      {/* Label + count */}
      <div className="flex items-center justify-between px-4 pt-4 pb-2">
        <span className="text-xs font-mono tracking-widest uppercase" style={{ color: "#555" }}>
          Conversas
        </span>
        {!isLoading && conversations.length > 0 && (
          <span className="text-xs font-mono text-vscode-muted">
            {conversations.length}
          </span>
        )}
      </div>

      {/* Lista */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <p className="px-4 py-2 text-xs text-vscode-muted font-mono animate-pulse">
            carregando...
          </p>
        ) : conversations.length === 0 ? (
          <div className="px-4 py-3">
            <p className="text-xs font-mono" style={{ color: "#444" }}>
              nenhuma conversa
            </p>
            <p className="text-[10px] font-mono mt-0.5" style={{ color: "#333" }}>
              pressione + para começar
            </p>
          </div>
        ) : (
          <div className="py-1">
            {conversations.map((conv) => {
              const isActive = conv.id === activeId;
              return (
                <button
                  key={conv.id}
                  onClick={() => onSelect(conv.id)}
                  className={`
                    group w-full text-left px-4 py-2.5 text-sm font-mono
                    transition-all duration-150
                    flex items-center gap-2.5
                    border-l-2
                    ${isActive
                      ? "border-vscode-blue text-vscode-text"
                      : "border-transparent hover:border-vscode-border"
                    }
                  `}
                  style={{
                    background: isActive ? "#1a1a1a" : "transparent",
                    color: isActive ? "#cccccc" : "#666",
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) (e.currentTarget as HTMLButtonElement).style.color = "#999";
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) (e.currentTarget as HTMLButtonElement).style.color = "#666";
                  }}
                >
                  <span
                    className="shrink-0 text-xs"
                    style={{ color: isActive ? "#3b78ff" : "#444" }}
                  >
                    {isActive ? "❯" : "○"}
                  </span>
                  <span className="truncate flex-1">{conv.title}</span>
                  {onDelete && (
                    <button
                      onClick={(e) => { e.stopPropagation(); onDelete(conv.id); }}
                      className="shrink-0 opacity-0 group-hover:opacity-100 hover:!text-red-400 transition-opacity text-xs ml-1"
                      style={{ color: "#555" }}
                      title="Deletar conversa"
                    >
                      ✕
                    </button>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Rodapé — modelo ativo */}
      <div className="px-4 py-3 flex items-center gap-1.5" style={{ borderTop: "1px solid #1a1a1a" }}>
        <span className="w-1.5 h-1.5 rounded-full bg-green-500 shrink-0" />
        <span className="text-xs font-mono truncate" style={{ color: "#444" }}>Qwen3.5-9B</span>
      </div>

      {/* Botão fechar — só aparece no mobile */}
      <button
        onClick={onClose}
        className="absolute top-3 right-3 text-vscode-muted hover:text-white font-mono text-sm md:hidden"
      >
        ✕
      </button>

    </aside>
    </>
  );
}
