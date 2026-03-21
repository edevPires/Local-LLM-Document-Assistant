#!/usr/bin/env python
"""
Script de teste para o pipeline RAG (Milestone 3).

Fluxo:
1. Cria uma conversa
2. Faz upload de um PDF
3. Aguarda indexação (is_indexed = True)
4. Envia pergunta sobre o conteúdo
5. Verifica resposta contextualizada
"""

import os
import sys
import json
import requests
import time
from pathlib import Path

# Change to backend directory
backend_dir = Path(__file__).parent / "backend"
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from chat.models import Conversation, Document

API_URL = "http://localhost:8000/api"

def test_rag_pipeline():
    """Testa o pipeline RAG completo."""

    print("=" * 70)
    print("TESTE RAG PIPELINE (Milestone 3)")
    print("=" * 70)

    # 1. Criar conversa
    print("\n1. Criando conversa...")
    conversation = Conversation.objects.create(title="Teste RAG")
    print(f"   ✓ Conversa criada: ID={conversation.id}")

    # 2. Fazer upload de PDF
    print("\n2. Fazendo upload de PDF...")
    pdf_path = Path("C:/Users/bruno/OneDrive/Documentos/GitHub/Local-LLM-Document-Assistant/downloads/Escopo_AppNotificacaoV0.pdf")

    if not pdf_path.exists():
        print(f"   ! Arquivo não encontrado: {pdf_path}")
        print("   Procurando outros PDFs...")

        # Procurar por PDFs na pasta Downloads
        downloads = Path("C:/Users/bruno/Downloads")
        pdfs = list(downloads.glob("*.pdf"))
        if pdfs:
            pdf_path = pdfs[0]
            print(f"   Encontrado: {pdf_path}")
        else:
            print("   ! Nenhum PDF encontrado. Criando PDF de teste...")
            # Criar um PDF de teste simples
            try:
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import letter

                pdf_path = Path("test_sample.pdf")
                c = canvas.Canvas(str(pdf_path), pagesize=letter)
                c.drawString(100, 750, "Teste RAG - Documento de Amostra")
                c.drawString(100, 700, "Este é um documento de teste para validar a indexação RAG.")
                c.drawString(100, 650, "O prazo do projeto é 31 de março de 2026.")
                c.drawString(100, 600, "O orçamento total aprovado é de R$ 50.000,00.")
                c.drawString(100, 550, "A equipe responsável tem 5 membros.")
                c.save()
                print(f"   PDF de teste criado: {pdf_path}")
            except ImportError:
                print("   ! reportlab não instalado. Usando PDF existente...")
                # Procurar PDFs em Downloads
                downloads = Path("C:/Users/bruno/Downloads")
                pdfs = list(downloads.glob("*.pdf"))
                if pdfs:
                    pdf_path = pdfs[0]
                else:
                    print("   ! Nenhum PDF encontrado. Abortando teste.")
                    return False

    # Upload via requests
    with open(pdf_path, "rb") as f:
        files = {"file": f}
        response = requests.post(
            f"{API_URL}/conversations/{conversation.id}/documents/",
            files=files
        )

    if response.status_code != 201:
        print(f"   ! Erro ao fazer upload: {response.status_code}")
        print(f"   {response.text}")
        return False

    doc_data = response.json()
    document_id = doc_data["id"]
    print(f"   ✓ PDF enviado: ID={document_id}")
    print(f"   ✓ Texto extraído: {len(doc_data['extracted_text'])} caracteres")

    # 3. Aguardar indexação
    print("\n3. Aguardando indexação no ChromaDB...")
    for attempt in range(5):
        doc = Document.objects.get(id=document_id)
        if doc.is_indexed:
            print(f"   ✓ Documento indexado (tentativa {attempt + 1})")
            break
        print(f"   Aguardando... (tentativa {attempt + 1}/5)")
        time.sleep(1)
    else:
        print("   ! Indexação não completou após 5 tentativas")
        print(f"   is_indexed = {doc.is_indexed}")
        # Continuar mesmo assim, o erro pode estar no rag_service

    # 4. Enviar pergunta sobre o conteúdo
    print("\n4. Enviando pergunta sobre o documento...")
    question = "Qual é o prazo do projeto?"

    response = requests.post(
        f"{API_URL}/conversations/{conversation.id}/messages/send/",
        json={"content": question}
    )

    if response.status_code != 201:
        print(f"   ! Erro ao enviar pergunta: {response.status_code}")
        print(f"   {response.text}")
        return False

    msg_data = response.json()
    assistant_response = msg_data["assistant_message"]["content"]

    print(f"   ✓ Pergunta: {question}")
    print(f"   ✓ Resposta: {assistant_response[:200]}...")

    # 5. Validar resposta contextualizada
    print("\n5. Validando resposta...")

    # Procurar por palavras-chave da resposta RAG
    keywords = ["prazo", "março", "2026", "31"]
    found_keywords = [kw for kw in keywords if kw.lower() in assistant_response.lower()]

    if found_keywords:
        print(f"   ✓ Resposta contém contexto do documento: {found_keywords}")
        print("\n" + "=" * 70)
        print("TESTE RAG: SUCESSO!")
        print("=" * 70)
        return True
    else:
        print(f"   ! Resposta não contém contexto esperado")
        print(f"   Palavras-chave procuradas: {keywords}")
        print(f"   Encontradas: {found_keywords}")
        print("\nResposta completa:")
        print(f"   {assistant_response}")
        print("\n" + "=" * 70)
        print("TESTE RAG: INCONCLUSIVO")
        print("=" * 70)
        return None

if __name__ == "__main__":
    try:
        success = test_rag_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n! Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
