"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Message } from "@/types";
import { FileAttachmentCard } from "./FileAttachmentCard";

function parseAttachment(content: string): { filename: string; text: string } | null {
  if (!content.startsWith("📎 ")) return null;
  const rest = content.slice(3);
  const sep = rest.indexOf("\n\n");
  if (sep === -1) return { filename: rest.trim(), text: "" };
  return { filename: rest.slice(0, sep).trim(), text: rest.slice(sep + 2) };
}

interface Props {
  message: Message;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";
  const time = new Date(message.created_at).toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  if (isUser) {
    const attachment = parseAttachment(message.content);

    return (
      <div className="flex w-full mb-4 justify-end">
        <div className="flex flex-col max-w-[75%] items-end gap-1.5">
          {attachment ? (
            <>
              <FileAttachmentCard filename={attachment.filename} />
              {attachment.text && (
                <div className="px-4 py-2 text-sm font-mono leading-relaxed break-words bg-vscode-user-msg text-white rounded rounded-br-none whitespace-pre-wrap w-full">
                  {attachment.text}
                </div>
              )}
            </>
          ) : (
            <div className="px-4 py-2 text-sm font-mono leading-relaxed break-words bg-vscode-user-msg text-white rounded rounded-br-none whitespace-pre-wrap">
              {message.content}
            </div>
          )}
          <span className="text-[10px] text-vscode-muted font-mono">
            {time}
          </span>
        </div>
      </div>
    );
  }

  // Substitui <br> e <br/> por quebra de linha real para o markdown parser
  const processedContent = message.content.replace(/<br\s*\/?>/gi, "\n");

  return (
    <div className="flex w-full mb-5 justify-start">
      <span className="text-vscode-blue text-xs mr-3 mt-0.5 shrink-0 font-mono">
        QW›
      </span>
      <div className="flex flex-col min-w-0 flex-1 max-w-[80%]">
        <div className="text-sm font-mono leading-relaxed text-vscode-text break-words">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({ children }) => <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>,
              strong: ({ children }) => (
                <strong className="text-vscode-blue font-bold">{children}</strong>
              ),
              em: ({ children }) => (
                <em className="text-vscode-muted italic">{children}</em>
              ),
              h1: ({ children }) => (
                <h1 className="text-base font-bold text-white mt-4 mb-2 pb-1 border-b border-vscode-border">
                  {children}
                </h1>
              ),
              h2: ({ children }) => (
                <h2 className="text-sm font-bold text-white mt-4 mb-2 pb-1 border-b border-vscode-border">
                  {children}
                </h2>
              ),
              h3: ({ children }) => (
                <h3 className="text-sm font-semibold mt-3 mb-1" style={{ color: "#3b78ff" }}>
                  {children}
                </h3>
              ),
              ul: ({ children }) => (
                <ul className="mb-3 pl-4 space-y-1.5" style={{ listStyleType: "none" }}>
                  {children}
                </ul>
              ),
              ol: ({ children }) => (
                <ol className="mb-3 pl-4 space-y-1.5 list-decimal">
                  {children}
                </ol>
              ),
              li: ({ children }) => (
                <li className="text-vscode-text flex gap-2 items-start">
                  <span className="mt-[5px] shrink-0 w-1.5 h-1.5 rounded-full bg-vscode-blue inline-block" />
                  <span>{children}</span>
                </li>
              ),
              code: ({ children, className }) => {
                const isBlock = className?.includes("language-");
                return isBlock ? (
                  <code className="block bg-vscode-bg border border-vscode-border px-3 py-2 my-2 text-xs overflow-x-auto whitespace-pre">
                    {children}
                  </code>
                ) : (
                  <code className="bg-vscode-active border border-vscode-border px-1 text-vscode-blue text-xs">
                    {children}
                  </code>
                );
              },
              pre: ({ children }) => <>{children}</>,
              table: ({ children }) => (
                <div className="overflow-x-auto my-3">
                  <table className="w-full border-collapse text-xs font-mono">
                    {children}
                  </table>
                </div>
              ),
              thead: ({ children }) => (
                <thead style={{ background: "#1a1a1a" }}>{children}</thead>
              ),
              tbody: ({ children }) => <tbody>{children}</tbody>,
              tr: ({ children }) => (
                <tr className="border-b" style={{ borderColor: "#2a2a2a" }}>{children}</tr>
              ),
              th: ({ children }) => (
                <th className="text-left px-3 py-2 font-semibold" style={{ color: "#aaaaaa", borderBottom: "1px solid #3b78ff" }}>
                  {children}
                </th>
              ),
              td: ({ children }) => (
                <td className="px-3 py-2 text-vscode-text align-top" style={{ borderRight: "1px solid #1e1e1e" }}>
                  {children}
                </td>
              ),
              blockquote: ({ children }) => (
                <blockquote className="border-l-2 border-vscode-blue pl-3 my-2 text-vscode-muted italic">
                  {children}
                </blockquote>
              ),
              hr: () => <hr className="border-vscode-border my-3" />,
              a: ({ children, href }) => (
                <a
                  href={href}
                  className="text-vscode-blue underline"
                  target="_blank"
                  rel="noreferrer"
                >
                  {children}
                </a>
              ),
            }}
          >
            {processedContent}
          </ReactMarkdown>
        </div>
        <span className="text-[10px] text-vscode-muted font-mono mt-1">
          {time}
        </span>
      </div>
    </div>
  );
}
