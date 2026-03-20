"""
Django settings for Local LLM Document Assistant.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Caminho raiz do monorepo (um nível acima do backend/)
ROOT_DIR = BASE_DIR.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-h_t7i82f05t9b2ccqiz)mucca&mgn$@ym9&xzwt&di3cj8v&(("

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]


# ============================================================
# Apps
# ============================================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    # Local
    "chat",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # CORS deve ser o primeiro
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# ============================================================
# Database — SQLite para simplicidade
# ============================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ============================================================
# CORS — Permite o frontend Next.js (localhost:3000) acessar a API
# ============================================================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


# ============================================================
# Django REST Framework
# ============================================================
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}


# ============================================================
# Internacionalização
# ============================================================
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True


# ============================================================
# Arquivos estáticos e mídia (uploads)
# ============================================================
STATIC_URL = "static/"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================================================
# LLM Configuration
# ============================================================

# URL do llama-server (processo externo com o modelo carregado na GPU)
# Rodar antes do Django:
#   C:\Users\bruno\llama.cpp\build\bin\llama-server.exe \
#       --model backend/models/Qwen3.5-9B-Q4_K_M.gguf \
#       --n-gpu-layers -1 --ctx-size 4096 --port 8080
LLM_SERVER_URL = os.environ.get("LLM_SERVER_URL", "http://127.0.0.1:8080")

# Temperatura: controla a "criatividade" do modelo.
# 0.0 = determinístico (sempre a mesma resposta)
# 1.0 = muito criativo (mais variação)
# 0.7 = bom equilíbrio
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.7"))

# Máximo de tokens gerados por resposta.
# Qwen3.5 com thinking mode usa ~1000-1500 tokens para raciocínio interno.
# 4096 garante espaço suficiente para thinking + resposta completa.
LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "4096"))


# ============================================================
# RAG — ChromaDB Vector Store (Milestone 3)
# ============================================================
CHROMA_DB_PATH = str(BASE_DIR / "chroma_db")
