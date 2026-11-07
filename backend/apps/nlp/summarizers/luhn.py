"""
Sumarizador de Luhn (1958) — algoritmo atual do TechCurator e baseline do estudo.

Conforme a Equação (1) do relatório, a pontuação de uma sentença é a soma das
frequências normalizadas de seus tokens significativos (após remoção de
stopwords):

    score(s) = Σ_{w∈s} freq(w) / freq_max

onde freq(w) é o nº de ocorrências do termo w no texto inteiro e freq_max é a
frequência do termo mais frequente. As sentenças de maior pontuação compõem o
resumo.
"""
from collections import Counter

from ..utils import tokenize
from .base import BaseSummarizer


class LuhnSummarizer(BaseSummarizer):
    name = "luhn"

    def _term_frequencies(self, sentences: list[str]):
        freq: Counter[str] = Counter()
        for sent in sentences:
            freq.update(tokenize(sent))
        freq_max = max(freq.values()) if freq else 1
        return freq, freq_max

    def _rank_sentences(self, sentences: list[str]) -> list[tuple[int, float]]:
        freq, freq_max = self._term_frequencies(sentences)
        scores: list[tuple[int, float]] = []
        for i, sent in enumerate(sentences):
            tokens = tokenize(sent)
            if not tokens:
                scores.append((i, 0.0))
                continue
            # Equação (1): soma das frequências normalizadas dos tokens.
            score = sum(freq[w] / freq_max for w in tokens)
            scores.append((i, score))
        return scores
