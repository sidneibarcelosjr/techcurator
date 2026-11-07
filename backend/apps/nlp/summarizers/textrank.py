"""
Sumarizador TextRank (Mihalcea & Tarau, 2004) — Equações 4 e 5 do relatório.

As sentenças são nós de um grafo; as arestas recebem peso proporcional à
similaridade por cosseno dos vetores TF-IDF das sentenças:

    sim(s_i, s_j) = (v_i · v_j) / (||v_i|| · ||v_j||)               (4)

O ranking final é dado pelo PageRank iterativo, com fator de amortecimento
d = 0,85:

    score(s_i) = (1 - d) + d · Σ_{j∈viz(i)} [ w_ij / Σ_k w_jk ] · score(s_j)  (5)
"""
import math
from collections import Counter

from ..utils import tokenize
from .base import BaseSummarizer


class TextRankSummarizer(BaseSummarizer):
    name = "textrank"

    DAMPING = 0.85
    ITERATIONS = 50
    EPS = 1e-6

    # ---- vetores TF-IDF das sentenças -------------------------------------
    def _tfidf_vectors(self, sentences: list[str]) -> list[dict[str, float]]:
        tokenized = [tokenize(s) for s in sentences]
        n_docs = len(sentences)
        df: Counter[str] = Counter()
        for toks in tokenized:
            for term in set(toks):
                df[term] += 1
        idf = {t: math.log(n_docs / df[t]) + 1.0 if df[t] else 0.0 for t in df}

        vectors: list[dict[str, float]] = []
        for toks in tokenized:
            tf = Counter(toks)
            total = len(toks) or 1
            vectors.append({w: (tf[w] / total) * idf.get(w, 0.0) for w in tf})
        return vectors

    @staticmethod
    def _cosine(vi: dict[str, float], vj: dict[str, float]) -> float:
        if not vi or not vj:
            return 0.0
        common = set(vi) & set(vj)
        dot = sum(vi[w] * vj[w] for w in common)
        if dot == 0.0:
            return 0.0
        ni = math.sqrt(sum(v * v for v in vi.values()))
        nj = math.sqrt(sum(v * v for v in vj.values()))
        return dot / (ni * nj) if ni and nj else 0.0

    def _rank_sentences(self, sentences: list[str]) -> list[tuple[int, float]]:
        n = len(sentences)
        vectors = self._tfidf_vectors(sentences)

        # Matriz de similaridade por cosseno — Equação (4).
        weights = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                sim = self._cosine(vectors[i], vectors[j])
                weights[i][j] = sim
                weights[j][i] = sim

        out_sum = [sum(weights[i]) or 1.0 for i in range(n)]

        # PageRank iterativo — Equação (5).
        scores = [1.0 / n] * n
        for _ in range(self.ITERATIONS):
            new_scores = [(1.0 - self.DAMPING)] * n
            for i in range(n):
                acc = 0.0
                for j in range(n):
                    if weights[j][i] > 0:
                        acc += (weights[j][i] / out_sum[j]) * scores[j]
                new_scores[i] += self.DAMPING * acc
            delta = sum(abs(new_scores[k] - scores[k]) for k in range(n))
            scores = new_scores
            if delta < self.EPS:
                break

        return [(i, scores[i]) for i in range(n)]
