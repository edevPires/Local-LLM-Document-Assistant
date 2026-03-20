"""
Serializers — Converte modelos Django para JSON (e vice-versa).

=== CONCEITO ===

No Django REST Framework, os Serializers têm duas funções principais:

1. SERIALIZAÇÃO (Model → JSON):
   Quando o frontend faz GET /api/conversations/, o Django busca as
   conversas no banco e precisa transformar em JSON para enviar.
   O Serializer define quais campos incluir no JSON.

2. DESERIALIZAÇÃO (JSON → Model):
   Quando o frontend faz POST /api/conversations/ com {"title": "Minha Conversa"},
   o Serializer valida os dados e cria o objeto no banco.

ModelSerializer é um atalho que gera os campos automaticamente
baseado no modelo Django. Basta dizer qual modelo e quais campos.
"""

from rest_framework import serializers
from .models import Conversation, Message, Document


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializa uma mensagem.

    CONCEITO: 'fields' define o que aparece no JSON de resposta.
    Se você não quer expor um campo, basta não listar aqui.

    'read_only_fields' são campos que o cliente NÃO pode definir
    via POST/PUT — o Django preenche automaticamente.
    """

    class Meta:
        model = Message
        fields = ["id", "conversation", "role", "content", "created_at"]
        read_only_fields = ["id", "created_at"]


class DocumentSerializer(serializers.ModelSerializer):
    """
    Serializa um documento.

    'extracted_text' é read_only porque é gerado pelo backend.
    'summary' também é read_only porque é gerado pelo LLM.
    """

    class Meta:
        model = Document
        fields = [
            "id",
            "conversation",
            "file",
            "original_filename",
            "extracted_text",
            "summary",
            "is_indexed",
            "uploaded_at",
        ]
        read_only_fields = [
            "id",
            "original_filename",
            "extracted_text",
            "summary",
            "is_indexed",
            "uploaded_at",
        ]


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializa uma conversa.

    CONCEITO: 'message_count' é um SerializerMethodField — um campo
    calculado que não existe no banco de dados. Ele chama o método
    get_message_count() para calcular o valor dinamicamente.

    Isso é útil para mostrar "12 mensagens" na sidebar sem precisar
    carregar todas as mensagens na resposta.
    """

    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "title", "created_at", "updated_at", "message_count"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_message_count(self, obj):
        """Retorna o número de mensagens na conversa."""
        return obj.messages.count()
