"""
Configurações Django do projeto TechCurator.
"""
import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env(key, default=None):
    return os.environ.get(key, default)


def env_bool(key, default=False):
    val = os.environ.get(key)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "on")


def env_list(key, default=""):
    raw = os.environ.get(key, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


SECRET_KEY = env("SECRET_KEY", "dev-insecure-change-me")
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1,backend")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceiros
    "rest_framework",
    "corsheaders",
    "django_celery_beat",
    # Apps locais
    "apps.accounts",
    "apps.news",
    "apps.scraping",
    "apps.nlp",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "curadoria.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "curadoria.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", "curadoria_db"),
        "USER": env("DB_USER", "curadoria_user"),
        "PASSWORD": env("DB_PASSWORD", "curadoria_dev_senha"),
        "HOST": env("DB_HOST", "db"),
        "PORT": env("DB_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ----------------------------------------------------------------------------
# Django REST Framework + JWT
# ----------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 24,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
}

# ----------------------------------------------------------------------------
# CORS
# ----------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
)

# ----------------------------------------------------------------------------
# Celery
# ----------------------------------------------------------------------------
CELERY_BROKER_URL = env("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", "redis://redis:6379/1")
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# ----------------------------------------------------------------------------
# Configuração do pipeline de NLP
# ----------------------------------------------------------------------------
# Método de sumarização padrão. Escalável: troque por "tfidf" ou "textrank"
# (ou defina a env SUMMARIZER_METHOD) para testar os outros métodos.
SUMMARIZER_METHOD = env("SUMMARIZER_METHOD", "luhn")
SUMMARY_SENTENCES = int(env("SUMMARY_SENTENCES", "3"))

# Limiar mínimo de relevância tech — cenário Moderado (aplicado 2026-09-08).
# Portais generalistas (G1, Exame, Folha Tec...): precisam atingir 0.20.
# Elevado de 0.15 → 0.20 com base no diagnóstico de distribuição de scores.
TECH_RELEVANCE_THRESHOLD = float(env("TECH_RELEVANCE_THRESHOLD", "0.20"))

# Limiar para portais is_tech_specialized=True (TecMundo, Canaltech...).
# Substitui o bypass total anterior — artigos com score < 0.08 são descartados
# mesmo vindo de fontes especializadas (ex.: culinária, streaming no TechTudo).
# Para reverter ao bypass absoluto: TECH_RELEVANCE_THRESHOLD_SPECIALIZED=0.0
TECH_RELEVANCE_THRESHOLD_SPECIALIZED = float(
    env("TECH_RELEVANCE_THRESHOLD_SPECIALIZED", "0.08")
)

# ----------------------------------------------------------------------------
# Clustering de notícias (agrupamento por fato cross-source)
# ----------------------------------------------------------------------------
# Limiar de similaridade de cosseno para agrupar notícias como "mesmo fato".
CLUSTERING_THRESHOLD = float(env("CLUSTERING_THRESHOLD", "0.30"))
# Janela temporal padrão do clustering periódico (horas).
CLUSTERING_WINDOW_HOURS = int(env("CLUSTERING_WINDOW_HOURS", "72"))

# ----------------------------------------------------------------------------
# Estimativa de credibilidade
# ----------------------------------------------------------------------------
# Máximo que o consenso cross-source pode adicionar ao score textual base.
# O score base é determinado pelos sinais textuais; o consenso é apenas bônus.
# Com 0.25: texto "low" (base < 0.33) + bônus máximo nunca alcança "high".
CREDIBILITY_CONSENSUS_BONUS_MAX = float(env("CREDIBILITY_CONSENSUS_BONUS_MAX", "0.25"))
# Limiar superior: score >= este valor → label "high".
CREDIBILITY_THRESHOLD_HIGH = float(env("CREDIBILITY_THRESHOLD_HIGH", "0.66"))
# Limiar inferior: score >= este valor → "medium"; abaixo → "low".
CREDIBILITY_THRESHOLD_LOW = float(env("CREDIBILITY_THRESHOLD_LOW", "0.33"))
