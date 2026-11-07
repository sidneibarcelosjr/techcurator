"""
Arquitetura escalável de sumarização extrativa.

O sistema é desenhado para suportar múltiplos métodos de sumarização de
forma intercambiável. Cada sumarizador herda de `BaseSummarizer` e é
registrado no `REGISTRY`. O método ativo é definido por
`settings.SUMMARIZER_METHOD` (padrão: "luhn") ou pela env `SUMMARIZER_METHOD`.

Métodos disponíveis:
  - "luhn"     → LuhnSummarizer     (padrão; clássico de Luhn, 1958)
  - "tfidf"    → TfidfSummarizer    (pontuação por TF-IDF das sentenças)
  - "textrank" → TextRankSummarizer (grafo de similaridade + PageRank)

Para adicionar um novo método basta criar uma subclasse de `BaseSummarizer`,
definir `name` e implementar `summarize`, depois registrá-la em `REGISTRY`.
"""
from abc import ABC, abstractmethod

from ..utils import split_sentences


class BaseSummarizer(ABC):
    """Interface comum a todos os sumarizadores extrativos."""

    name: str = "base"

    def __init__(self, num_sentences: int = 3):
        self.num_sentences = max(1, num_sentences)

    @abstractmethod
    def _rank_sentences(self, sentences: list[str]) -> list[tuple[int, float]]:
        """
        Recebe a lista de sentenças e retorna pares (indice, pontuacao).
        Não precisa estar ordenado.
        """
        raise NotImplementedError

    def summarize(self, text: str) -> str:
        """Gera um resumo extrativo preservando a ordem original das sentenças."""
        sentences = split_sentences(text)
        if not sentences:
            return ""
        if len(sentences) <= self.num_sentences:
            return " ".join(sentences)

        scored = self._rank_sentences(sentences)
        # Seleciona as N melhores...
        top = sorted(scored, key=lambda x: x[1], reverse=True)[: self.num_sentences]
        # ...e as reordena pela posição original (legibilidade).
        chosen_idx = sorted(idx for idx, _ in top)
        return " ".join(sentences[i] for i in chosen_idx)
