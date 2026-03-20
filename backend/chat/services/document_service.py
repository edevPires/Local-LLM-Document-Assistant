"""
Document Service — Extração de texto de arquivos PDF e DOCX.

=== CONCEITO ===

Antes de enviar um documento ao LLM, precisamos extrair o texto puro.
O LLM não consegue ler arquivos binários (PDF/DOCX) — ele só processa texto.

Fluxo:
    Upload do arquivo (PDF ou DOCX)
        ↓
    document_service.extract_text(file)
        ↓
    Texto puro (string)
        ↓
    llm_service.summarize(texto)
        ↓
    Resumo salvo no banco

=== BIBLIOTECAS ===

- PyPDF2: lê arquivos PDF página por página e extrai o texto
- python-docx: lê arquivos DOCX parágrafo por parágrafo

=== LIMITAÇÕES ===

- PDFs escaneados (imagens): PyPDF2 não consegue extrair texto (precisaria de OCR)
- Tabelas complexas: podem virar texto desorganizado
- Fórmulas matemáticas: perdem formatação
"""

import logging
from pathlib import Path

import PyPDF2

logger = logging.getLogger(__name__)


def extract_text(file_path: str) -> str:
    """
    Extrai texto de um arquivo PDF ou DOCX.

    CONCEITO: Detecta o tipo do arquivo pela extensão e delega
    para a função correta de extração.

    Args:
        file_path: caminho absoluto do arquivo no disco

    Returns:
        str: texto extraído do documento

    Raises:
        ValueError: se o formato do arquivo não for suportado
        Exception: se a extração falhar
    """
    path = Path(file_path)
    extension = path.suffix.lower()

    logger.info("Extraindo texto de '%s' (formato: %s)", path.name, extension)

    if extension == ".pdf":
        return _extract_from_pdf(str(path))
    elif extension in (".docx", ".doc"):
        return _extract_from_docx(str(path))
    else:
        raise ValueError(
            f"Formato não suportado: '{extension}'. "
            "Use PDF (.pdf) ou Word (.docx)."
        )


def _extract_from_pdf(file_path: str) -> str:
    """
    Extrai texto de um arquivo PDF usando PyPDF2.

    CONCEITO: Um PDF é dividido em páginas. PyPDF2 itera cada página
    e chama extract_text() em cada uma, retornando o texto puro.

    Exemplo:
        PDF com 3 páginas:
            Página 1: "Introdução..."
            Página 2: "Desenvolvimento..."
            Página 3: "Conclusão..."

        Retorna: "Introdução...\n\nDesenvolvimento...\n\nConclusão..."
    """
    

    pages_text = []

    with open(file_path, "rb") as f:  # "rb" = read binary (PDF é binário)
        reader = PyPDF2.PdfReader(f)
        total_pages = len(reader.pages)

        logger.info("PDF com %d páginas", total_pages)

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                pages_text.append(text.strip())
            else:
                logger.warning("Página %d não tem texto extraível", i + 1)

    full_text = "\n\n".join(pages_text)

    if not full_text.strip():
        raise ValueError(
            "Não foi possível extrair texto do PDF. "
            "O arquivo pode ser um PDF escaneado (imagem). "
            "Use um PDF com texto selecionável."
        )

    logger.info("Extraídos %d caracteres do PDF", len(full_text))
    return full_text


def _extract_from_docx(file_path: str) -> str:
    """
    Extrai texto de um arquivo DOCX usando python-docx.

    CONCEITO: Um DOCX é composto de parágrafos. python-docx itera
    cada parágrafo e extrai o texto de cada um.

    Exemplo:
        DOCX com 3 parágrafos:
            "Título do Documento"
            "Primeiro parágrafo com conteúdo..."
            "Segundo parágrafo com mais detalhes..."

        Retorna: "Título do Documento\n\nPrimeiro parágrafo...\n\nSegundo parágrafo..."
    """
    from docx import Document

    doc = Document(file_path)

    paragraphs = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:  # Ignora parágrafos vazios
            paragraphs.append(text)

    full_text = "\n\n".join(paragraphs)

    if not full_text.strip():
        raise ValueError("O arquivo DOCX está vazio ou não contém texto.")

    logger.info("Extraídos %d caracteres do DOCX", len(full_text))
    return full_text
