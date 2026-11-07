"""
Pipeline de NLP: orquestra classificação, sumarização, extração de keywords,
geração do hash de deduplicação e estimativa inicial de credibilidade para
cada artigo coletado.
"""
from dataclasses import dataclass, field

from django.conf import settings

from .classifier import classify
from .credibility import compute_credibility, text_credibility_score
from .keyword_extractor import extract_keywords
from .summarizers import get_summarizer
from .utils import clean_text, content_hash


@dataclass
class NLPResult:
    relevance_score: float
    is_tech: bool
    summary: str
    keywords: list[str]
    matched_terms: list[str]
    dedup_hash: str
    summarizer_method: str
    credibility_score: float | None
    credibility_label: str
    text_signal_score: float | None = None
    extra: dict = field(default_factory=dict)


def process_article(
    *,
    title: str,
    content: str,
    url: str,
    trusted_source: bool = False,
    method: str | None = None,
) -> NLPResult:
    """
    Executa o pipeline completo de NLP sobre um artigo.

    `trusted_source=True` indica portais is_tech_specialized=True. Antes,
    esses portais bypassavam o filtro por completo. Agora aplicamos um
    threshold MAIS BAIXO (TECH_RELEVANCE_THRESHOLD_SPECIALIZED) em vez do
    bypass total — permite bloquear conteúdo sem qualquer sinal tech mesmo
    vindo de portais especializados, sem descartar artigos legítimos.

    Thresholds configuráveis via env/settings:
      TECH_RELEVANCE_THRESHOLD_SPECIALIZED  (padrão 0.08) — portais esp.
      TECH_RELEVANCE_THRESHOLD              (padrão 0.15) — portais generalistas

    A credibilidade inicial é calculada apenas com os sinais textuais
    (coverage=1, sem consenso externo ainda). A tarefa periódica de
    clustering atualiza o score com o componente de consenso cross-source.
    """
    full_text = f"{title}. {content}".strip()

    # 1. Classificação de relevância tech
    relevance, matched = classify(full_text)

    # Threshold diferenciado: especializados têm margem mais baixa (mas não zero).
    # Para reverter ao bypass total: defina TECH_RELEVANCE_THRESHOLD_SPECIALIZED=0.0
    if trusted_source:
        threshold = getattr(settings, "TECH_RELEVANCE_THRESHOLD_SPECIALIZED", 0.08)
    else:
        threshold = getattr(settings, "TECH_RELEVANCE_THRESHOLD", 0.20)
    is_tech = relevance >= threshold

    # 2. Sumarização extrativa (Luhn)
    method = method or getattr(settings, "SUMMARIZER_METHOD", "luhn")
    n_sent = getattr(settings, "SUMMARY_SENTENCES", 3)
    summarizer = get_summarizer(method=method, num_sentences=n_sent)
    cleaned = clean_text(content or title)
    summary = summarizer.summarize(cleaned)

    # 3. Extração de palavras-chave
    keywords = extract_keywords(full_text, top_n=6)

    # 4. Hash de deduplicação
    dedup = content_hash(title, url)

    # 5. Credibilidade inicial (somente sinais textuais; coverage=1 → consenso zero)
    cred_score, cred_label = compute_credibility(
        title=title, content=content, coverage=1
    )
    text_signal = round(text_credibility_score(title, content), 4)

    return NLPResult(
        relevance_score=round(relevance, 4),
        is_tech=is_tech,
        summary=summary,
        keywords=keywords,
        matched_terms=matched,
        dedup_hash=dedup,
        summarizer_method=summarizer.name,
        credibility_score=cred_score,
        credibility_label=cred_label,
        text_signal_score=text_signal,
    )
