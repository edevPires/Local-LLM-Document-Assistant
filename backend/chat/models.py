"""
Modelos de dados do chat.

CONCEITO: No Django, cada classe Model vira uma tabela no banco de dados.
Cada atributo da classe vira uma coluna na tabela.

Temos 3 modelos:
- Conversation: uma conversa (como um "chat" no ChatGPT)
- Message: uma mensagem dentro de uma conversa (do usuário ou do assistente)
- Document: um arquivo enviado pelo usuário (PDF/DOCX)
"""

from django.db import models


class Conversation(models.Model):
    """
    Uma conversa é um container de mensagens.
    Exemplo: "Conversa sobre Python", "Resumo do relatório Q4"

    No banco, gera a tabela: chat_conversation
    """

    title = models.CharField(
        max_length=255,
        default="Nova Conversa",
        help_text="Título da conversa, exibido na sidebar",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]  # Mais recentes primeiro

    def __str__(self):
        return f"[{self.id}] {self.title}"


class Message(models.Model):
    """
    Uma mensagem dentro de uma conversa.

    CONCEITO: ForeignKey cria uma relação "muitos-para-um".
    Cada mensagem pertence a UMA conversa, mas uma conversa tem MUITAS mensagens.
    'related_name' permite acessar as mensagens de uma conversa:
        conversa.messages.all()

    CONCEITO: 'choices' limita os valores possíveis para o campo 'role'.
    Isso funciona como um ENUM no banco.
    """

    ROLE_CHOICES = [
        ("user", "Usuário"),
        ("assistant", "Assistente"),
        ("system", "Sistema"),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,  # Se deletar a conversa, deleta as mensagens
        related_name="messages",
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        help_text="Quem enviou: user, assistant, ou system",
    )
    content = models.TextField(
        help_text="O conteúdo da mensagem",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]  # Ordem cronológica

    def __str__(self):
        return f"[{self.role}] {self.content[:50]}..."


class Document(models.Model):
    """
    Um documento enviado pelo usuário para resumo/análise.

    CONCEITO: FileField armazena o arquivo no disco (MEDIA_ROOT/documents/)
    e salva o caminho relativo no banco de dados.

    'is_indexed' será usado na Milestone 3 (ChromaDB)
    para saber se já geramos embeddings deste documento.
    """

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    file = models.FileField(
        upload_to="documents/",
        help_text="Arquivo PDF ou DOCX enviado",
    )
    original_filename = models.CharField(
        max_length=255,
        help_text="Nome original do arquivo (ex: relatorio.pdf)",
    )
    extracted_text = models.TextField(
        blank=True,
        default="",
        help_text="Texto extraído do documento (gerado automaticamente)",
    )
    summary = models.TextField(
        blank=True,
        null=True,
        help_text="Resumo gerado pelo LLM",
    )
    is_indexed = models.BooleanField(
        default=False,
        help_text="Se o documento já foi indexado no ChromaDB (Milestone 3)",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.original_filename} ({self.conversation.title})"
