"""
BaseSpider: coleta RSS-first com fallback para extração HTML.

Cada spider declara `source_slug`, `source_name`, `feed_url` (RSS) e,
opcionalmente, `is_tech_specialized`. O parsing de RSS é feito por
`feedparser`; quando o feed não traz conteúdo/imagem, há um fallback
opcional que baixa a página e extrai com BeautifulSoup.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone as dt_timezone
from time import mktime

import feedparser
import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 TechCuratorBot/1.0"
)
REQUEST_TIMEOUT = 15


@dataclass
class ScrapedItem:
    title: str
    url: str
    content: str = ""
    image_url: str = ""
    published_at: datetime | None = None
    source_slug: str = ""
    source_name: str = ""
    is_tech_specialized: bool = False
    raw: dict = field(default_factory=dict)


def _clean_html(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


class BaseSpider:
    source_slug: str = ""
    source_name: str = ""
    feed_url: str = ""
    base_url: str = ""
    is_tech_specialized: bool = False
    # Faz uma requisição extra à página para enriquecer conteúdo/imagem.
    fetch_full_page: bool = False
    max_items: int = 30

    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    # ----------------------------------------------------------------- RSS
    def _parse_published(self, entry) -> datetime | None:
        for key in ("published_parsed", "updated_parsed"):
            value = getattr(entry, key, None) or entry.get(key)
            if value:
                try:
                    return datetime.fromtimestamp(mktime(value), tz=dt_timezone.utc)
                except Exception:
                    continue
        return None

    def _extract_image(self, entry) -> str:
        # media:content / media:thumbnail
        media = entry.get("media_content") or entry.get("media_thumbnail")
        if media and isinstance(media, list) and media:
            url = media[0].get("url")
            if url:
                return url
        # enclosures
        for link in entry.get("links", []):
            if link.get("rel") == "enclosure" and "image" in link.get("type", ""):
                return link.get("href", "")
        # primeira <img> no summary
        summary = entry.get("summary", "") or entry.get("description", "")
        match = re.search(r'<img[^>]+src="([^"]+)"', summary)
        if match:
            return match.group(1)
        return ""

    def _entry_content(self, entry) -> str:
        if entry.get("content"):
            return _clean_html(entry["content"][0].get("value", ""))
        return _clean_html(entry.get("summary", "") or entry.get("description", ""))

    # ----------------------------------------------------- fallback HTML
    def _fetch_page(self, url: str) -> tuple[str, str]:
        """Retorna (texto_limpo, image_url) baixando a página."""
        try:
            resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except Exception:
            return "", ""
        soup = BeautifulSoup(resp.content, "lxml")

        # og:image
        og = soup.find("meta", property="og:image")
        image = og["content"] if og and og.get("content") else ""

        # Tenta o corpo do artigo
        article = soup.find("article") or soup.find("main") or soup.body
        text = ""
        if article:
            paragraphs = article.find_all("p")
            text = " ".join(p.get_text(" ", strip=True) for p in paragraphs)
            text = re.sub(r"\s+", " ", text).strip()
        return text, image

    # ----------------------------------------------------------------- API
    def fetch(self) -> list[ScrapedItem]:
        """Coleta e retorna a lista de itens do feed (com fallback)."""
        items: list[ScrapedItem] = []
        if not self.feed_url:
            return items
        try:
            parsed = feedparser.parse(
                self.feed_url,
                request_headers={"User-Agent": USER_AGENT},
            )
        except Exception:
            return items

        for entry in parsed.entries[: self.max_items]:
            title = (entry.get("title") or "").strip()
            url = (entry.get("link") or "").strip()
            if not title or not url:
                continue

            content = self._entry_content(entry)
            image = self._extract_image(entry)

            if self.fetch_full_page and (len(content) < 200 or not image):
                page_text, page_image = self._fetch_page(url)
                if len(page_text) > len(content):
                    content = page_text
                if not image:
                    image = page_image

            items.append(
                ScrapedItem(
                    title=title,
                    url=url,
                    content=content,
                    image_url=image,
                    published_at=self._parse_published(entry),
                    source_slug=self.source_slug,
                    source_name=self.source_name,
                    is_tech_specialized=self.is_tech_specialized,
                )
            )
        return items
