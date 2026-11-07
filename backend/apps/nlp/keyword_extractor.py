"""
Extrator de palavras-chave: combina unigramas e bigramas por frequência,
com *boost* para termos presentes no léxico tech.
"""
from collections import Counter

from .classifier import TECH_LEXICON
from .utils import strip_accents, tokenize

_LEXICON_TERMS = {strip_accents(t) for t in TECH_LEXICON}


def extract_keywords(text: str, top_n: int = 6) -> list[str]:
    """Extrai as `top_n` palavras-chave mais relevantes do texto."""
    tokens = tokenize(text)
    if not tokens:
        return []

    counts: Counter[str] = Counter()

    # Unigramas
    for tok in tokens:
        counts[tok] += 1

    # Bigramas
    for a, b in zip(tokens, tokens[1:]):
        counts[f"{a} {b}"] += 1

    # Boost para termos do léxico tech
    boosted: Counter[str] = Counter()
    for term, freq in counts.items():
        weight = freq
        norm = strip_accents(term)
        if norm in _LEXICON_TERMS:
            weight *= 3
        # Bigramas recebem leve preferência por serem mais específicos.
        if " " in term:
            weight = weight * 1.3
        boosted[term] = weight

    ranked = [term for term, _ in boosted.most_common(top_n * 2)]

    # Remove unigramas que já aparecem dentro de um bigrama selecionado.
    bigrams = [t for t in ranked if " " in t]
    bigram_words = {w for bg in bigrams for w in bg.split()}
    result: list[str] = []
    for term in ranked:
        if " " not in term and term in bigram_words:
            continue
        result.append(term)
        if len(result) >= top_n:
            break
    return result
