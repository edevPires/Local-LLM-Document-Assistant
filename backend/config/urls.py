"""
URLs raiz do projeto.

CONCEITO: Este arquivo é o "ponto de entrada" das URLs.
Tudo que chega ao Django passa por aqui primeiro.

Estrutura:
  /admin/  → Django Admin (interface de gerenciamento)
  /api/    → Endpoints da API REST (chat, conversas, etc.)
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("chat.urls")),
]

# Em desenvolvimento, o Django serve os arquivos de mídia (uploads)
# Em produção, um servidor como Nginx faz isso.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
