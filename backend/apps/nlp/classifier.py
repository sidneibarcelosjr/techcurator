"""
Classificador de tecnologia baseado em léxico ponderado em pt-BR.

Aborda o problema de forma *explicável*: cada termo carrega um peso e a
pontuação final é a soma normalizada dos pesos dos termos encontrados.
"""
from .utils import strip_accents

# Léxico ponderado (~90 termos). Termos sem acento — o texto é normalizado
# antes da comparação.
TECH_LEXICON: dict[str, float] = {
    # Núcleo de IA / dados
    "inteligencia artificial": 3.0, "machine learning": 3.0,
    "aprendizado de maquina": 3.0, "deep learning": 3.0,
    "rede neural": 2.5, "redes neurais": 2.5, "chatgpt": 3.0, "openai": 2.5,
    "gpt": 2.5, "llm": 2.5, "modelo de linguagem": 2.5, "gemini": 2.5,
    "claude": 2.0, "copilot": 2.0, "algoritmo": 2.0, "dados": 1.0,
    "big data": 2.0, "ciencia de dados": 2.5, "automacao": 1.5,
    # Hardware
    "chip": 2.0, "processador": 2.0, "gpu": 2.0, "cpu": 2.0, "semicondutor": 2.5,
    "placa de video": 2.0, "nvidia": 2.0, "amd": 1.5, "intel": 1.5,
    "qualcomm": 2.0, "snapdragon": 2.0, "ram": 1.5, "ssd": 1.5,
    "computacao quantica": 3.0, "robô": 1.5, "robotica": 2.0, "drone": 1.5,
    # Dispositivos
    "smartphone": 2.0, "celular": 1.5, "iphone": 2.0, "android": 2.0,
    "ios": 1.5, "tablet": 1.5, "notebook": 1.5, "laptop": 1.5,
    "smartwatch": 2.0, "wearable": 2.0, "console": 1.5, "playstation": 1.5,
    "xbox": 1.5, "nintendo": 1.5, "realidade virtual": 2.5,
    "realidade aumentada": 2.5, "metaverso": 2.0, "oculos": 1.0,
    # Software / dev
    "software": 2.0, "aplicativo": 1.5, "app": 1.0, "sistema operacional": 2.0,
    "windows": 1.5, "linux": 2.0, "macos": 1.5, "codigo": 1.5,
    "programacao": 2.0, "desenvolvedor": 2.0, "open source": 2.0,
    "codigo aberto": 2.0, "api": 1.5, "framework": 1.5, "github": 2.0,
    # Internet / nuvem / infra
    "nuvem": 1.5, "cloud": 1.5, "aws": 2.0, "azure": 2.0, "servidor": 1.5,
    "data center": 2.5, "5g": 2.0, "wifi": 1.0, "banda larga": 1.5,
    "fibra optica": 1.5, "internet": 1.0, "rede": 0.8,
    # Segurança
    "ciberseguranca": 2.5, "seguranca digital": 2.5, "hacker": 2.0,
    "ransomware": 2.5, "malware": 2.5, "phishing": 2.0, "vazamento": 1.5,
    "criptografia": 2.0, "vulnerabilidade": 1.5, "ataque cibernetico": 2.5,
    # Web3 / fintech
    "bitcoin": 2.0, "criptomoeda": 2.5, "blockchain": 2.5, "ethereum": 2.0,
    "nft": 2.0, "fintech": 2.0, "pix": 1.0, "carteira digital": 1.5,
    # Empresas / plataformas
    "google": 1.5, "apple": 1.5, "microsoft": 1.5, "meta": 1.5,
    "amazon": 1.0, "tesla": 1.5, "spacex": 1.5, "samsung": 1.5,
    "tiktok": 1.5, "instagram": 1.0, "whatsapp": 1.5, "startup": 1.5,
    "tecnologia": 1.5, "digital": 0.8, "inovacao": 1.0, "gadget": 1.5,
}

# Pontuação máxima teórica usada para normalizar em [0, 1].
_NORM_CAP = 12.0


def classify(text: str) -> tuple[float, list[str]]:
    """
    Retorna (relevance_score em [0,1], termos_encontrados).

    A pontuação é a soma dos pesos dos termos do léxico presentes no texto,
    normalizada por uma constante e truncada em 1.0.
    """
    haystack = strip_accents((text or "").lower())
    score = 0.0
    matched: list[str] = []
    for term, weight in TECH_LEXICON.items():
        if term in haystack:
            score += weight
            matched.append(term)
    relevance = min(score / _NORM_CAP, 1.0)
    return relevance, matched
