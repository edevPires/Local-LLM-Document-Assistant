"""
Admin — Registra os modelos no Django Admin.

CONCEITO: O Django Admin é uma interface web automática para
gerenciar os dados do banco. Ao registrar um modelo aqui,
você pode acessar /admin/ e criar, editar, deletar registros
sem precisar de código.

Útil para debug e para verificar o que está no banco.
"""

from django.contrib import admin
from .models import Conversation, Message, Document


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "created_at", "updated_at"]
    search_fields = ["title"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["id", "conversation", "role", "content_preview", "created_at"]
    list_filter = ["role", "conversation"]

    def content_preview(self, obj):
        return obj.content[:80] + "..." if len(obj.content) > 80 else obj.content
    content_preview.short_description = "Conteúdo"


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["id", "original_filename", "conversation", "is_indexed", "uploaded_at"]
    list_filter = ["is_indexed"]
