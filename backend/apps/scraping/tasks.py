"""Tarefas Celery do scraping."""
from celery import shared_task

from .orchestrator import run_scraping


@shared_task(name="scraping.run_all")
def run_all_task():
    """Executa o scraping de todas as fontes. Agendável via Celery Beat."""
    return run_scraping()


@shared_task(name="scraping.run_source")
def run_source_task(source_slug: str):
    """Executa o scraping de uma única fonte."""
    return run_scraping(source_slug=source_slug)
