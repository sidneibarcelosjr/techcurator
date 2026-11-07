"""Configuração do Celery para o projeto TechCurator."""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "curadoria.settings")

app = Celery("curadoria")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
