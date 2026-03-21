"use client";

interface Props {
  filename: string;
}

function PdfIcon() {
  return (
    <svg width="40" height="48" viewBox="0 0 40 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Corpo do documento */}
      <path d="M4 0H28L40 12V44C40 46.2 38.2 48 36 48H4C1.8 48 0 46.2 0 44V4C0 1.8 1.8 0 4 0Z" fill="#dc2626" />
      {/* Canto dobrado */}
      <path d="M28 0L40 12H32C29.8 12 28 10.2 28 8V0Z" fill="#b91c1c" />
      {/* Texto PDF */}
      <text x="20" y="34" textAnchor="middle" fill="white" fontSize="11" fontWeight="bold" fontFamily="monospace">PDF</text>
    </svg>
  );
}

function DocxIcon() {
  return (
    <svg width="40" height="48" viewBox="0 0 40 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Corpo do documento */}
      <path d="M4 0H28L40 12V44C40 46.2 38.2 48 36 48H4C1.8 48 0 46.2 0 44V4C0 1.8 1.8 0 4 0Z" fill="#2563eb" />
      {/* Canto dobrado */}
      <path d="M28 0L40 12H32C29.8 12 28 10.2 28 8V0Z" fill="#1d4ed8" />
      {/* Letra W */}
      <text x="20" y="34" textAnchor="middle" fill="white" fontSize="16" fontWeight="bold" fontFamily="monospace">W</text>
    </svg>
  );
}

function GenericIcon() {
  return (
    <svg width="40" height="48" viewBox="0 0 40 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M4 0H28L40 12V44C40 46.2 38.2 48 36 48H4C1.8 48 0 46.2 0 44V4C0 1.8 1.8 0 4 0Z" fill="#374151" />
      <path d="M28 0L40 12H32C29.8 12 28 10.2 28 8V0Z" fill="#1f2937" />
      {/* Linhas de texto genéricas */}
      <rect x="8" y="22" width="24" height="2" rx="1" fill="#9ca3af" />
      <rect x="8" y="28" width="18" height="2" rx="1" fill="#9ca3af" />
      <rect x="8" y="34" width="20" height="2" rx="1" fill="#9ca3af" />
    </svg>
  );
}

export function FileAttachmentCard({ filename }: Props) {
  const ext = filename.split(".").pop()?.toLowerCase() ?? "";

  const Icon =
    ext === "pdf" ? PdfIcon :
    ext === "docx" || ext === "doc" ? DocxIcon :
    GenericIcon;

  const label =
    ext === "pdf" ? "PDF" :
    ext === "docx" || ext === "doc" ? "Word" :
    ext.toUpperCase() || "Arquivo";

  return (
    <div
      className="flex items-center gap-3 px-3 py-3 rounded transition-colors duration-150 max-w-[280px]"
      style={{ background: "#161616", border: "1px solid #2a2a2a", cursor: "default" }}
      onMouseEnter={(e) => { (e.currentTarget as HTMLDivElement).style.borderColor = "#3b78ff"; }}
      onMouseLeave={(e) => { (e.currentTarget as HTMLDivElement).style.borderColor = "#2a2a2a"; }}
    >
      <div className="shrink-0">
        <Icon />
      </div>
      <div className="flex flex-col min-w-0">
        <span className="text-white text-sm font-mono font-medium truncate leading-tight">
          {filename}
        </span>
        <span className="text-xs font-mono mt-0.5" style={{ color: "#555" }}>
          {label}
        </span>
      </div>
    </div>
  );
}
