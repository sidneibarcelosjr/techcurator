"""
Estimativa de indícios de credibilidade de notícias.

Combina duas evidências:

  1. SINAIS TEXTUAIS (base) — presença de padrões associados a baixa ou alta
     credibilidade:
     • Clickbait no título (caixa-alta excessiva, pontuação exclamativa,
       frases-isca, listas numéricas manipulativas).
     • Linguagem de oferta/promoção no título (termos de deal, lojas varejistas
       combinadas com preço/desconto).
     • Linguagem alarmista/sensacionalista no título + texto.
     • Atribuição de fonte no texto (bônus: "segundo", "declarou", aspas).

  2. CONSENSO CROSS-SOURCE (bônus) — quantas fontes distintas cobrem o mesmo
     fato (derivado do cluster). Funciona como bônus limitado sobre o score
     base textual; NÃO é o eixo principal do score.

Score final em [0, 1]:
  base  = text_credibility_score(title, content)   ← score textual isolado
  bonus = consensus_score(coverage) × CONSENSUS_BONUS_MAX
  credibility_score = min(base + bonus, 1.0)

Comportamento garantido:
  • Artigo isolado (coverage=1): avaliado apenas pelos sinais textuais.
    Uma notícia sóbria isolada NÃO é penalizada por estar isolada.
  • Consenso alto NUNCA transforma texto de baixa qualidade em "high":
    com CONSENSUS_BONUS_MAX ≤ THRESHOLD_HIGH − THRESHOLD_LOW, um texto
    abaixo de THRESHOLD_LOW não pode alcançar THRESHOLD_HIGH por bônus
    de consenso (veto implícito por aritmética).
  • Conteúdo de oferta/promoção apelativos é detectado e penalizado como
    sinal de baixa qualidade jornalística, mesmo com alta cobertura.

Mapeado em três faixas (rótulos):
  "high"   (score ≥ THRESHOLD_HIGH)  → 🟢 alta credibilidade
  "medium" (score ≥ THRESHOLD_LOW)   → 🟡 credibilidade média
  "low"    (score <  THRESHOLD_LOW)  → 🔴 baixa credibilidade

RESTRIÇÃO METODOLÓGICA: a identidade ou reputação da fonte NÃO entra no
cálculo — apenas consenso e sinais de conteúdo. Isso evita circularidade
e torna o modelo agnóstico quanto às fontes.
"""
from __future__ import annotations

import re

from .utils import strip_accents

# ---------------------------------------------------------------------------
# Parâmetros padrão (sobrescritos via settings / env)
# ---------------------------------------------------------------------------

# Máximo que o consenso pode adicionar ao score textual base.
# Com valor 0.25 e limiares 0.33/0.66, garante o veto implícito:
#   texto "low" (base < 0.33) + bônus máximo (0.25) < 0.58 < 0.66 → nunca "high".
CONSENSUS_BONUS_MAX = 0.25

THRESHOLD_HIGH = 0.66
THRESHOLD_LOW = 0.33


# ===========================================================================
# 1. Score de consenso cross-source (bônus)
# ===========================================================================

def consensus_score(coverage: int) -> float:
    """
    Converte cobertura (nº de fontes distintas no cluster) em [0, 1].

    coverage = 1 → 0.00  (isolada; bônus zero — avaliada só pelo texto)
    coverage = 2 → 0.33
    coverage = 3 → 0.67
    coverage ≥ 4 → 1.00

    O bônus efetivo é consensus_score × CONSENSUS_BONUS_MAX.
    """
    if coverage <= 1:
        return 0.0
    return min((coverage - 1) / 3.0, 1.0)


# ===========================================================================
# 2. Score textual
# ===========================================================================

# 2a. Clickbait no título ---------------------------------------------------

_CLICKBAIT_PHRASES = [
    r"\bvoc[eê]\s+n[aã]o\s+vai\s+acreditar\b",
    r"\bvoc[eê]\s+precisa\s+(ver|saber|conhecer)\b",
    r"\bisso\s+vai\s+mudar\b",
    r"\bo\s+segredo\s+(que|por\s+tr[aá]s)\b",
    r"\bningu[eé]m\s+(te\s+conta|fala)\b",
    r"\b\d+\s+(raz[oõ]es|motivos|dicas|formas|segredos|truques|maneiras)\b",
    r"\bpor\s+que\s+\d+\b",
    r"\bveja\s+(agora|j[aá])[!\s]",
    r"\bdescubra\s+(agora|j[aá])[!\s]",
    r"\burgente[!:]",
    r"\balerta[!:]",
    r"\bchocante\b",
    r"\bincrível\b",
    r"\bexclusiv[oa][!]",
    r"\bnão\s+vai\s+acreditar\b",
]
_CLICKBAIT_RE = re.compile("|".join(_CLICKBAIT_PHRASES), re.IGNORECASE)


def _clickbait_penalty(title: str) -> float:
    """Penalidade por clickbait no título [0, 1]."""
    if not title:
        return 0.0
    t_norm = strip_accents(title).lower()
    penalty = 0.0

    # Caixa-alta excessiva (> 40 % das letras são maiúsculas)
    letters = [c for c in title if c.isalpha()]
    if letters and sum(1 for c in letters if c.isupper()) / len(letters) > 0.4:
        penalty += 0.30

    # Pontuação exclamativa excessiva (> 2 ocorrências)
    if title.count("!") > 2:
        penalty += 0.20

    # Frases e padrões clickbait
    if _CLICKBAIT_RE.search(t_norm):
        penalty += 0.40

    return min(penalty, 1.0)


# 2b. Linguagem de oferta/promoção no título --------------------------------
#
# Detecta conteúdo promocional de baixa qualidade jornalística.
# Estrutura em dois grupos: termos de deal e nomes de varejistas.
# A penalidade é maior quando ambos coincidem no título (ex: "Amazon joga
# preço no chão") do que quando apenas um está presente.

_OFFER_DEAL_PATTERNS = [
    r"\boferta[s]?\b",                            # oferta / ofertas
    r"\bpromoca(o|oes)\b",                        # promoção / promoções (strip_accents)
    r"\bdescontos?\b",                            # desconto / descontos
    r"\bcupo(m|ns)\b",                            # cupom / cupons (pt-BR)
    r"\bfrete\s+gratis\b",                        # frete grátis
    r"\bmais\s+barato[s]?\b",
    r"\bpreco\s+(no\s+chao|baixo|minimo|historico)\b",   # preço no chão etc.
    r"\bjog(a|ou)\s+preco\b",                     # joga/jogou preço
    r"\bderrub(a|ou)\s+preco\b",                  # derruba/derrubou preço
    r"\b\d+x\s+sem\s+juros\b",                    # 12x sem juros (parcelamento)
    r"\bparcelado\b",                              # parcelado em X vezes
    r"\b\d+\s*%\s*(off|de\s+desconto)\b",
    r"\bblack\s+friday\b",
    r"\bcyber\s+monday\b",
    r"\bpromoca(o|oes)\s+relampago\b",            # promoção relâmpago
    r"\bqueima\s+de\s+estoque\b",                 # queima de estoque
]
_OFFER_DEAL_RE = re.compile("|".join(_OFFER_DEAL_PATTERNS), re.IGNORECASE)

# Varejistas/marketplaces (fabricantes como Apple/Samsung não entram).
_OFFER_STORES_RE = re.compile(
    r"\b(amazon|mercado\s+livre|magalu|magazine\s+luiza|shopee|americanas"
    r"|submarino|casas\s+bahia|fast\s+shop|kabum|aliexpress)\b",
    re.IGNORECASE,
)

# Menção explícita de preço em reais (usado como sinal auxiliar).
_OFFER_PRICE_RE = re.compile(r"\br\$\s*[\d.,]+", re.IGNORECASE)


def _offer_penalty(title: str) -> float:
    """
    Penalidade por linguagem de oferta/promoção no título [0, 0.40].

    Escala:
      deal_term + varejista → 0.40  (ex: "Amazon joga preço no chão")
      deal_term (sem varejista) → 0.25  (ex: "50% OFF no notebook")
      varejista + preço (sem deal_term) → 0.25  (ex: "Amazon: TV por R$ 999")
      nenhum padrão → 0.00

    O valor 0.40 para deal+store garante o veto implícito: mesmo com o bônus
    máximo de atribuição (+0.30) e consenso (+0.25), o score final não
    ultrapassa 0.65 < THRESHOLD_HIGH (0.66).
    """
    if not title:
        return 0.0
    t_norm = strip_accents(title).lower()

    has_deal = bool(_OFFER_DEAL_RE.search(t_norm))
    has_store = bool(_OFFER_STORES_RE.search(t_norm))
    has_price = bool(_OFFER_PRICE_RE.search(t_norm))

    if has_deal and has_store:
        return 0.40
    if has_deal:
        return 0.25
    if has_store and has_price:
        # Varejista + menção de preço sem linguagem explícita de deal
        # ainda sinaliza conteúdo promocional.
        return 0.25
    return 0.0


# 2c. Linguagem sensacionalista / alarmista ---------------------------------

_SENSATIONALISM_TERMS = {
    "catastrofe", "apocalipse", "colapso", "caos total", "fim do mundo",
    "desastre", "tragedia", "emergencia",
    "invasao", "ataque massivo", "guerra cibernetica", "espionagem total",
    "roubo de dados massivo", "vigilancia em massa",
    "escandalo", "fraude massiva", "corrupcao",
    "chocante", "absurdo", "vergonhoso", "criminoso",
    "manipulacao", "censura total", "banimento",
}


def _sensationalism_penalty(text: str) -> float:
    """Penalidade por linguagem sensacionalista [0, 0.3]."""
    if not text:
        return 0.0
    normalized = strip_accents(text).lower()
    hits = sum(1 for term in _SENSATIONALISM_TERMS if term in normalized)
    return min(hits * 0.10, 0.30)


# 2d. Atribuição de fonte (bônus) ------------------------------------------

_ATTRIBUTION_PATTERNS = [
    r"\bsegundo\b",
    r"\bde\s+acordo\s+com\b",
    r"\bafirmou\b",
    r"\bdeclarou\b",
    r"\bconfirmou\b",
    r"\binformou\b",
    r"\bdisse\b",
    r"\baponta\b",
    r"\bpublicou\b",
    r"\bdivulg(ou|aram)\b",
    r'"[^"]{10,}"',          # citação direta entre aspas (mínimo 10 chars)
]
_ATTRIBUTION_RE = re.compile("|".join(_ATTRIBUTION_PATTERNS), re.IGNORECASE)


def _attribution_bonus(text: str) -> float:
    """Bônus por atribuição de fonte no corpo do texto [0, 0.3]."""
    if not text:
        return 0.0
    hits = len(_ATTRIBUTION_RE.findall(text))
    # 1 marcador → +0.10, 2 → +0.20, 3+ → +0.30
    return min(hits * 0.10, 0.30)


def text_credibility_score(title: str, content: str) -> float:
    """
    Score de credibilidade textual em [0, 1].

    Parte de 0.5 (neutro), aplica penalidades por clickbait, linguagem de
    oferta/promoção e sensacionalismo, e bônus por atribuição de fonte.

    O bônus de atribuição é suprimido quando há penalidade de oferta ativa:
    citações como "segundo a Amazon" em artigos promocionais não aumentam a
    credibilidade jornalística — são atribuições à própria fonte comercial.
    """
    score = 0.5
    score -= _clickbait_penalty(title)
    offer_pen = _offer_penalty(title)
    score -= offer_pen
    score -= _sensationalism_penalty(f"{title} {content}")
    if not offer_pen:
        score += _attribution_bonus(content or title)
    return max(0.0, min(score, 1.0))


# ===========================================================================
# 3. Score final e faixa
# ===========================================================================

def _load_settings():
    """Carrega parâmetros de settings (com fallback para constantes)."""
    try:
        from django.conf import settings
        return (
            getattr(settings, "CREDIBILITY_CONSENSUS_BONUS_MAX", CONSENSUS_BONUS_MAX),
            getattr(settings, "CREDIBILITY_THRESHOLD_HIGH", THRESHOLD_HIGH),
            getattr(settings, "CREDIBILITY_THRESHOLD_LOW", THRESHOLD_LOW),
        )
    except Exception:
        return CONSENSUS_BONUS_MAX, THRESHOLD_HIGH, THRESHOLD_LOW


def compute_credibility(
    title: str,
    content: str,
    coverage: int = 1,
) -> tuple[float, str]:
    """
    Calcula o score e o rótulo de credibilidade de um artigo.

    Parâmetros
    ----------
    title    : título do artigo
    content  : texto completo (ou resumo quando indisponível)
    coverage : nº de fontes distintas que cobrem o mesmo fato (do Cluster).
               Valor 1 = artigo isolado (sem bônus de consenso).

    Retorna
    -------
    (credibility_score: float em [0, 1], credibility_label: "high"|"medium"|"low")

    Fórmula
    -------
    base  = text_credibility_score(title, content)
    bonus = consensus_score(coverage) × consensus_bonus_max
    score = min(base + bonus, 1.0)

    O veto implícito garante que texto de baixa qualidade não alcance "high":
    com consensus_bonus_max = 0.25 e threshold_high = 0.66, um artigo com
    base < threshold_low (< 0.33) atinge no máximo 0.57 < 0.66.
    """
    bonus_max, th, tl = _load_settings()

    base = text_credibility_score(title, content)
    bonus = consensus_score(coverage) * bonus_max
    final = round(min(base + bonus, 1.0), 4)

    if final >= th:
        label = "high"
    elif final >= tl:
        label = "medium"
    else:
        label = "low"

    return final, label
