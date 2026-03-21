import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ResumeAI",
  description: "Assistente de documentos com IA local",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className="h-full">
      <body className="h-full">{children}</body>
    </html>
  );
}
