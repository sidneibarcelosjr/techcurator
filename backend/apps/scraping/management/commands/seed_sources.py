"""Comando: popula a tabela Source com os 23 portais catalogados."""
from django.core.management.base import BaseCommand

from apps.news.models import Source
from apps.scraping.spiders.sources import ALL_SPIDERS


class Command(BaseCommand):
    help = "Cria/atualiza as fontes de notícias no banco."

    def handle(self, *args, **options):
        created = 0
        for spider in ALL_SPIDERS:
            obj, was_created = Source.objects.update_or_create(
                slug=spider.source_slug,
                defaults={
                    "name": spider.source_name,
                    "base_url": getattr(spider, "base_url", ""),
                    "feed_url": getattr(spider, "feed_url", ""),
                    "is_tech_specialized": spider.is_tech_specialized,
                    "is_active": True,
                },
            )
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(
            f"{len(ALL_SPIDERS)} fontes processadas ({created} novas)."
        ))
