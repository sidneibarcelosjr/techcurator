"""Fachada de sumarização extrativa (resumo de notícias)."""
from django.conf import settings

from .summarizers import summarize as _summarize


def summarize(text: str, method: str | None = None, num_sentences: int | None = None) -> str:
    """Gera um resumo extrativo do texto usando o método Luhn."""
    method = method or getattr(settings, "SUMMARIZER_METHOD", "luhn")
    if num_sentences is None:
        num_sentences = getattr(settings, "SUMMARY_SENTENCES", 3)
    return _summarize(method, text or "", num_sentences)
