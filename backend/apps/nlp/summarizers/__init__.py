"""
Registro de sumarizadores extrativos.

O TechCurator usa o algoritmo de Luhn como sumarizador único de produção.
"""
from .base import BaseSummarizer
from .luhn import LuhnSummarizer

REGISTRY: dict[str, type[BaseSummarizer]] = {
    LuhnSummarizer.name: LuhnSummarizer,
}

DEFAULT_METHOD = "luhn"


def get_summarizer(method: str | None = None, num_sentences: int = 3) -> BaseSummarizer:
    """Retorna uma instância do sumarizador (único método disponível: Luhn)."""
    cls = REGISTRY.get((method or DEFAULT_METHOD).lower(), LuhnSummarizer)
    return cls(num_sentences=num_sentences)


def summarize(method: str, text: str, num_sentences: int = 3) -> str:
    """Gera um resumo extrativo usando Luhn."""
    return get_summarizer(method, num_sentences).summarize(text)


def available_methods() -> list[str]:
    return list(REGISTRY.keys())


__all__ = [
    "BaseSummarizer", "LuhnSummarizer",
    "REGISTRY", "get_summarizer", "summarize", "available_methods", "DEFAULT_METHOD",
]
