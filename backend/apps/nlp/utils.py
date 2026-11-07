"""
Utilidades de NLP: stopwords pt-BR, tokenização, segmentação de sentenças
e hashing para deduplicação.

Implementação propositalmente leve (sem dependência de modelos pré-treinados),
tornando o sistema explicável e executável em qualquer máquina sem GPU.
"""
import hashlib
import re
import unicodedata

# Stopwords em português (subconjunto curado + termos jornalísticos comuns).
STOPWORDS_PT = {
    "a", "à", "às", "ao", "aos", "aquela", "aquelas", "aquele", "aqueles",
    "aquilo", "as", "até", "com", "como", "da", "das", "de", "dela", "delas",
    "dele", "deles", "depois", "do", "dos", "e", "é", "ela", "elas", "ele",
    "eles", "em", "entre", "era", "eram", "essa", "essas", "esse", "esses",
    "esta", "está", "estas", "este", "estes", "eu", "foi", "foram", "há",
    "isso", "isto", "já", "lhe", "lhes", "mais", "mas", "me", "mesmo", "meu",
    "meus", "minha", "minhas", "muito", "na", "nas", "não", "nem", "no", "nos",
    "nós", "nossa", "nossas", "nosso", "nossos", "num", "numa", "o", "os", "ou",
    "para", "pela", "pelas", "pelo", "pelos", "por", "porque", "qual", "quando",
    "que", "quem", "são", "se", "sem", "ser", "seu", "seus", "só", "sob",
    "sobre", "sua", "suas", "também", "te", "tem", "tém", "ter", "teu", "teus",
    "tu", "tua", "tuas", "um", "uma", "umas", "uns", "você", "vocês", "vos",
    "ainda", "após", "ante", "cada", "contra", "desde", "durante", "outro",
    "outra", "outros", "outras", "todo", "toda", "todos", "todas", "ano",
    "anos", "dia", "dias", "vez", "vezes", "agora", "antes", "então", "assim",
    "deve", "pode", "podem", "vai", "ter", "foi", "fez", "diz", "disse",
}

_WORD_RE = re.compile(r"[a-zà-ÿ0-9]+", re.IGNORECASE)
# Segmentação de sentenças: ponto/!/? seguido de espaço e maiúscula.
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý])")


def strip_accents(text: str) -> str:
    """Remove acentuação para normalização (ex.: deduplicação por slug)."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize_title(title: str) -> str:
    """Normaliza um título para comparação/deduplicação."""
    title = strip_accents(title or "").lower()
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def tokenize(text: str) -> list[str]:
    """Tokeniza em palavras minúsculas, descartando stopwords e tokens curtos."""
    tokens = _WORD_RE.findall((text or "").lower())
    return [t for t in tokens if t not in STOPWORDS_PT and len(t) > 2]


def tokenize_keep_stop(text: str) -> list[str]:
    """Tokeniza sem descartar stopwords (útil para alguns sumarizadores)."""
    return _WORD_RE.findall((text or "").lower())


def split_sentences(text: str) -> list[str]:
    """Segmenta um texto em sentenças."""
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return []
    sentences = _SENT_SPLIT_RE.split(text)
    return [s.strip() for s in sentences if len(s.strip()) > 0]


def content_hash(title: str, url: str) -> str:
    """SHA-256 de título normalizado + URL para deduplicação."""
    base = f"{normalize_title(title)}|{(url or '').strip().lower()}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Limpeza de ruído publicitário e boilerplate (pré-processamento)
# ---------------------------------------------------------------------------
# Motivação (Seção 8.2 / 8.5 do relatório): textos coletados de portais
# frequentemente carregam frases de afiliação ("compre aqui"), chamadas para
# outras matérias ("leia também") e boilerplate ("assine a newsletter"). Se
# essas frases permanecem no texto-fonte, TODOS os sumarizadores tendem a
# pontuá-las e incluí-las nos resumos, derrubando o ROUGE de todos por igual
# e mascarando a diferença real entre os algoritmos. A limpeza é aplicada de
# forma idêntica antes dos três algoritmos, preservando a equidade da
# comparação.

# Padrões (em minúsculas, sem acento) que, se presentes numa sentença,
# indicam ruído a ser descartado. Conservador de propósito: só remove
# sentenças com forte sinal comercial/navegacional.
_NOISE_PATTERNS = [
    r"\bcompre\s+aqui\b",
    r"\bcompre\s+agora\b",
    r"\bclique\s+aqui\b",
    r"\bconfira\s+(a|o)\s+oferta",
    r"\bmelhor\s+pre[çc]o\b",
    r"\bfrete\s+gr[áa]tis\b",
    r"\bcupom\s+de\s+desconto\b",
    r"\bem\s+oferta\b",
    r"\bpor\s+apenas\s+r\$",
    r"\blink\s+de\s+afiliad",
    r"\bpublicidade\b",
    r"\bpublieditorial\b",
    r"\bconte[úu]do\s+patrocinad",
    r"\bleia\s+(tamb[ée]m|mais|a\s+seguir)\b",
    r"\bveja\s+(tamb[ée]m|mais)\b",
    r"\bconfira\s+tamb[ée]m\b",
    r"\bassine\s+(a\s+)?(nossa\s+)?newsletter\b",
    r"\bassine\s+o\b",
    r"\binscreva-?se\b",
    r"\bcadastre-?se\b",
    r"\bsiga(-nos)?\s+.{0,30}\b(instagram|twitter|facebook|tiktok|youtube|whatsapp|telegram|threads|bluesky)\b",
    r"\bnos\s+siga\b",
    r"\bbaixe\s+(o\s+)?(nosso\s+)?app\b",
    r"\bfa[çc]a\s+parte\s+do\s+(nosso\s+)?(grupo|canal)\b",
    r"\bentre\s+no\s+(nosso\s+)?(grupo|canal)\b",
    r"\ball\s+rights\s+reserved\b",
    r"\btodos\s+os\s+direitos\s+reservados\b",
    r"\bfoto:\s",
    r"\bimagem:\s",
    r"\breprodu[çc][ãa]o\b",
    r"\bcom\s+informa[çc][õo]es\s+d[eo]\b",
]
_NOISE_RE = re.compile("|".join(_NOISE_PATTERNS), re.IGNORECASE)


def _is_noise_sentence(sentence: str) -> bool:
    """True se a sentença tem forte sinal de propaganda/navegação/boilerplate."""
    s = strip_accents(sentence).lower()

    if _NOISE_RE.search(s):
        return True

    # Sentença dominada por caixa-alta ou com muitos '|' costuma ser menu/rodapé.
    letters = [c for c in sentence if c.isalpha()]
    if len(letters) >= 12:
        upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        if upper_ratio > 0.6:
            return True
    if sentence.count("|") >= 2 or sentence.count("•") >= 2:
        return True

    return False


def clean_text(text: str) -> str:
    """
    Remove sentenças de ruído (publicidade, boilerplate, chamadas de navegação)
    preservando o restante do texto na ordem original.

    Aplicada ANTES da sumarização, de forma idêntica para os três algoritmos.
    Se a limpeza esvaziar o texto (caso raro de texto totalmente ruidoso),
    retorna o texto original para não quebrar o pipeline.
    """
    if not text:
        return ""
    sentences = split_sentences(text)
    if not sentences:
        return text.strip()

    kept = [s for s in sentences if not _is_noise_sentence(s)]
    if not kept:
        return text.strip()
    return " ".join(kept)
