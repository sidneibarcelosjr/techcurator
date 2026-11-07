"""
Sumarizador TF-IDF Posicional (Equações 2 e 3 do relatório).

Combina a ponderação TF-IDF de cada token com um bônus posicional, partindo da
hipótese jornalística de que os parágrafos iniciais concentram as informações
mais relevantes:

    TF-IDF(w, d) = TF(w, d) × log(N / df(w))                         (2)
    score(s) = ( Σ_{w∈s} TF-IDF(w, d) ) × 1 / log(p + 1)            (3)

onde p é a posição da sentença (indexada a partir de 1). Aqui cada sentença é
tratada como um "documento" para o cálculo de df, seguindo a prática usual de
sumarização extrativa por TF-IDF de sentenças.

Implementação dupla: usa scikit-learn quando disponível e recorre a uma versão
manual caso contrário, mantendo o sistema funcional sem a dependência.
"""
import math
from collections import Counter

from ..utils import tokenize
from .base import BaseSummarizer


class TfidfSummarizer(BaseSummarizer):
    name = "tfidf"

    @staticmethod
    def _position_bonus(p_index_zero: int) -> float:
        # p indexado a partir de 1 -> 1 / log(p + 1).
        p = p_index_zero + 1
        return 1.0 / math.log(p + 1)

    def _rank_sentences(self, sentences: list[str]) -> list[tuple[int, float]]:
        try:
            tfidf_per_sentence = self._tfidf_sklearn(sentences)
        except Exception:
            tfidf_per_sentence = self._tfidf_manual(sentences)

        scores: list[tuple[int, float]] = []
        for i, base in enumerate(tfidf_per_sentence):
            scores.append((i, base * self._position_bonus(i)))
        return scores

    # ---- soma TF-IDF por sentença (scikit-learn) --------------------------
    def _tfidf_sklearn(self, sentences: list[str]) -> list[float]:
        from sklearn.feature_extraction.text import TfidfVectorizer

        vectorizer = TfidfVectorizer(
            tokenizer=tokenize, lowercase=True, token_pattern=None
        )
        matrix = vectorizer.fit_transform(sentences)
        return [float(matrix.getrow(i).sum()) for i in range(matrix.shape[0])]

    # ---- soma TF-IDF por sentença (fallback manual) -----------------------
    def _tfidf_manual(self, sentences: list[str]) -> list[float]:
        tokenized = [tokenize(s) for s in sentences]
        n_docs = len(sentences)
        df: Counter[str] = Counter()
        for toks in tokenized:
            for term in set(toks):
                df[term] += 1
        idf = {t: math.log(n_docs / df[t]) if df[t] else 0.0 for t in df}

        sums: list[float] = []
        for toks in tokenized:
            if not toks:
                sums.append(0.0)
                continue
            tf = Counter(toks)
            total = len(toks)
            sums.append(sum((tf[w] / total) * idf.get(w, 0.0) for w in tf))
        return sums
