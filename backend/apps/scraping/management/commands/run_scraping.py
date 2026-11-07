"""Comando: executa o pipeline de scraping + NLP + persistência."""
from django.core.management.base import BaseCommand

from apps.scraping.orchestrator import run_scraping


class Command(BaseCommand):
    help = "Coleta notícias de tecnologia, processa via NLP e persiste."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source", type=str, default=None,
            help="Slug de uma fonte específica (ex.: tecmundo).",
        )
        parser.add_argument(
            "--workers", type=int, default=8,
            help="Número de threads paralelas para coleta.",
        )

    def handle(self, *args, **options):
        source = options.get("source")
        workers = options.get("workers")
        self.stdout.write(self.style.NOTICE(
            f"Iniciando scraping {'da fonte ' + source if source else 'de todas as fontes'}..."
        ))
        stats = run_scraping(source_slug=source, max_workers=workers)
        self.stdout.write(self.style.SUCCESS(
            "Concluído: "
            f"{stats['created']} criados, {stats['duplicate']} duplicados, "
            f"{stats['discarded']} descartados, {stats['errors']} erros "
            f"({stats['sources']} fontes)."
        ))
