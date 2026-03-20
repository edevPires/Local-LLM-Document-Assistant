"""
URLs do app chat.

=== CONCEITO ===

O URL Router do Django mapeia URLs para Views.
Quando o frontend faz GET /api/conversations/, o Django
percorre essa lista até encontrar a URL correspondente
e chama a view associada.

DefaultRouter é um atalho do DRF que gera automaticamente
todas as URLs para um ViewSet:
  /api/conversations/        → list, create
  /api/conversations/{pk}/   → retrieve, update, destroy

As URLs de mensagens são registradas manualmente porque
são "aninhadas" dentro de uma conversa (conversations/{id}/messages/).
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

# Router automático para ViewSets
router = DefaultRouter()
router.register(r"conversations", views.ConversationViewSet)

urlpatterns = [
    # URLs geradas automaticamente pelo router (CRUD de conversas)
    path("", include(router.urls)),

    # URLs manuais para mensagens (aninhadas dentro de conversas)
    path(
        "conversations/<int:conversation_id>/messages/",
        views.list_messages,
        name="list-messages",
    ),
    path(
        "conversations/<int:conversation_id>/messages/send/",
        views.send_message,
        name="send-message",
    ),

    # Upload de documentos (PDF/DOCX) — Milestone 2
    path(
        "conversations/<int:conversation_id>/documents/",
        views.upload_document,
        name="upload-document",
    ),
]
