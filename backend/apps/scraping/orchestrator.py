"""
Orquestrador do pipeline de scraping.

Executa os spiders em paralelo (ThreadPool), passa cada item pelo pipeline de
NLP, deduplica por hash e persiste no banco. Retorna estatísticas da execução.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.utils import timezone

from apps.news.models import Article, Category, Source, Tag
from apps.nlp.pipeline import process_article

from .spiders.base import BaseSpider, ScrapedItem
from .spiders.sources import ALL_SPIDERS, SPIDERS_BY_SLUG

logger = logging.getLogger(__name__)

DEFAULT_CATEGORY = "Tecnologia"


def _ensure_source(item: ScrapedItem) -> Source:
    source, _ = Source.objects.get_or_create(
        slug=item.source_slug,
        defaults={
            "name": item.source_name,
            "is_tech_specialized": item.is_tech_specialized,
        },
    )
    return source


def _ensure_tags(keywords: list[str]) -> list[Tag]:
    tags: list[Tag] = []
    for kw in keywords:
        name = kw.strip()
        if not name:
            continue
        from django.utils.text import slugify

        slug = slugify(name)[:100]
        if not slug:
            continue
        tag, _ = Tag.objects.get_or_create(slug=slug, defaults={"name": name})
        tags.append(tag)
    return tags


def _run_one_spider(spider_cls: type[BaseSpider]) -> list[ScrapedItem]:
    try:
        return spider_cls().fetch()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Spider %s falhou: %s", spider_cls.__name__, exc)
        return []


def persist_item(item: ScrapedItem, default_category: Category) -> str:
    """
    Processa um item pelo NLP e persiste. Retorna o status:
    "created", "duplicate" ou "discarded".
    """
    result = process_article(
        title=item.title,
        content=item.content,
        url=item.url,
        trusted_source=item.is_tech_specialized,
    )

    if not result.is_tech:
        return "discarded"

    if Article.objects.filter(dedup_hash=result.dedup_hash).exists():
        return "duplicate"

    source = _ensure_source(item)
    article = Article.objects.create(
        source=source,
        category=default_category,
        title=item.title,
        url=item.url,
        image_url=item.image_url or "",
        content=item.content,
        summary=result.summary,
        relevance_score=result.relevance_score,
        summarizer_method=result.summarizer_method,
        dedup_hash=result.dedup_hash,
        credibility_score=result.credibility_score,
        credibility_label=result.credibility_label,
        text_signal_score=result.text_signal_score,
        published_at=item.published_at or timezone.now(),
    )
    tags = _ensure_tags(result.keywords)
    if tags:
        article.tags.set(tags)
    return "created"


def run_scraping(source_slug: str | None = None, max_workers: int = 8) -> dict:
    """
    Executa o scraping de todas as fontes (ou de uma específica) e persiste.
    Retorna um dicionário com estatísticas.
    """
    if source_slug:
        spider_cls = SPIDERS_BY_SLUG.get(source_slug)
        if not spider_cls:
            raise ValueError(f"Fonte desconhecida: {source_slug}")
        spiders = [spider_cls]
    else:
        spiders = ALL_SPIDERS

    default_category, _ = Category.objects.get_or_create(
        slug="tecnologia", defaults={"name": DEFAULT_CATEGORY}
    )

    stats = {"created": 0, "duplicate": 0, "discarded": 0,
             "errors": 0, "sources": len(spiders)}

    # Coleta em paralelo.
    all_items: list[ScrapedItem] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_run_one_spider, sc): sc for sc in spiders}
        for fut in as_completed(futures):
            all_items.extend(fut.result())

    logger.info("Coletados %d itens de %d fontes", len(all_items), len(spiders))

    # Persistência sequencial (transações no banco).
    for item in all_items:
        try:
            status = persist_item(item, default_category)
            stats[status] += 1
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao persistir %s: %s", item.url, exc)
            stats["errors"] += 1

    return stats
