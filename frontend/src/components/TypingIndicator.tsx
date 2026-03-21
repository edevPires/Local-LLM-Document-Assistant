"use client";

export function TypingIndicator() {
  return (
    <div className="flex justify-start mb-3 items-center">
      <span className="text-vscode-blue text-xs mr-3 shrink-0 font-mono">QW›</span>
      <div className="flex items-center gap-1.5">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="inline-block w-1 h-1 rounded-full bg-vscode-blue"
            style={{
              animation: "typing-bounce 1.2s ease-in-out infinite",
              animationDelay: `${i * 0.2}s`,
            }}
          />
        ))}
        <span className="text-xs font-mono ml-1" style={{ color: "#444" }}>trabalhando</span>
      </div>
    </div>
  );
}
