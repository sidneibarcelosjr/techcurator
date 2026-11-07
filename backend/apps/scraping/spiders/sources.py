"""
Catálogo de 23 spiders de portais brasileiros de tecnologia.

Adicionar um novo portal: crie uma subclasse de BaseSpider definindo
`source_slug`, `source_name`, `feed_url` (e `is_tech_specialized` quando for
100% tech), e inclua-a em `ALL_SPIDERS`. O restante do pipeline (persistência,
deduplicação, NLP) é automático.

Observação: feeds RSS de portais mudam de URL ao longo do tempo. Se algum feed
retornar vazio, ajuste o `feed_url` da classe correspondente. Feeds quebrados
são simplesmente ignorados — o sistema continua funcionando.
"""
from .base import BaseSpider


# ============================================================================
# Especializados em tecnologia (is_tech_specialized=True)
# ============================================================================
class TecMundoSpider(BaseSpider):
    source_slug = "tecmundo"
    source_name = "TecMundo"
    base_url = "https://www.tecmundo.com.br"
    feed_url = "https://rss.tecmundo.com.br/feed"
    is_tech_specialized = True


class OlharDigitalSpider(BaseSpider):
    source_slug = "olhar-digital"
    source_name = "Olhar Digital"
    base_url = "https://olhardigital.com.br"
    feed_url = "https://olhardigital.com.br/feed/"
    is_tech_specialized = True


class CanaltechSpider(BaseSpider):
    source_slug = "canaltech"
    source_name = "Canaltech"
    base_url = "https://canaltech.com.br"
    feed_url = "https://canaltech.com.br/rss/"
    is_tech_specialized = True


class TecnoblogSpider(BaseSpider):
    source_slug = "tecnoblog"
    source_name = "Tecnoblog"
    base_url = "https://tecnoblog.net"
    feed_url = "https://tecnoblog.net/feed/"
    is_tech_specialized = True


class MeioBitSpider(BaseSpider):
    source_slug = "meio-bit"
    source_name = "Meio Bit"
    base_url = "https://meiobit.com"
    feed_url = "https://meiobit.com/feed/"
    is_tech_specialized = True


class GizmodoBrasilSpider(BaseSpider):
    source_slug = "gizmodo-brasil"
    source_name = "Gizmodo Brasil"
    base_url = "https://gizmodo.uol.com.br"
    feed_url = "https://gizmodo.uol.com.br/feed/"
    is_tech_specialized = True


class AdrenalineSpider(BaseSpider):
    source_slug = "adrenaline"
    source_name = "Adrenaline"
    base_url = "https://www.adrenaline.com.br"
    feed_url = "https://www.adrenaline.com.br/feed/"
    is_tech_specialized = True


class HardwareSpider(BaseSpider):
    source_slug = "hardware"
    source_name = "Hardware.com.br"
    base_url = "https://www.hardware.com.br"
    feed_url = "https://www.hardware.com.br/feed/"
    is_tech_specialized = True


class MundoConectadoSpider(BaseSpider):
    source_slug = "mundo-conectado"
    source_name = "Mundo Conectado"
    base_url = "https://www.mundoconectado.com.br"
    feed_url = "https://www.mundoconectado.com.br/rss"
    is_tech_specialized = True


class ShowmetechSpider(BaseSpider):
    source_slug = "showmetech"
    source_name = "Showmetech"
    base_url = "https://www.showmetech.com.br"
    feed_url = "https://www.showmetech.com.br/feed/"
    is_tech_specialized = True


class OficinaDaNetSpider(BaseSpider):
    source_slug = "oficina-da-net"
    source_name = "Oficina da Net"
    base_url = "https://www.oficinadanet.com.br"
    feed_url = "https://www.oficinadanet.com.br/rss.xml"
    is_tech_specialized = True


class TheBrief24Spider(BaseSpider):
    source_slug = "thebrief24"
    source_name = "TheBrief24"
    base_url = "https://thebrief24.com"
    feed_url = "https://thebrief24.com/feed/"
    is_tech_specialized = True


# ============================================================================
# Seções de tecnologia de portais generalistas (is_tech_specialized=False)
# ============================================================================
class TiltUolSpider(BaseSpider):
    source_slug = "tilt-uol"
    source_name = "Tilt UOL"
    base_url = "https://www.uol.com.br/tilt"
    feed_url = "https://rss.uol.com.br/feed/tilt.xml"


class TechTudoSpider(BaseSpider):
    source_slug = "techtudo"
    source_name = "TechTudo"
    base_url = "https://www.techtudo.com.br"
    feed_url = "https://pox.globo.com/rss/techtudo/"
    is_tech_specialized = True


class G1TecnologiaSpider(BaseSpider):
    source_slug = "g1-tecnologia"
    source_name = "G1 Tecnologia"
    base_url = "https://g1.globo.com/tecnologia"
    feed_url = "https://g1.globo.com/rss/g1/tecnologia/"


class ExameTecnologiaSpider(BaseSpider):
    source_slug = "exame-tecnologia"
    source_name = "Exame Tecnologia"
    base_url = "https://exame.com/tecnologia"
    feed_url = "https://exame.com/feed/"


# InfoMoneyTecnologiaSpider DESATIVADA (2026-09-08).
# Motivo: o feed /feed/ entrega o portal inteiro — loterias (Lotofácil, Mega-Sena),
# política internacional, resultados financeiros (Ambev, EcoRodovias), pesquisas
# eleitorais. Feeds por seção (/consumo/tecnologia/feed/, /negocios/tecnologia/feed/)
# existem mas estão vazios (sem artigos desde 2006 — são feeds de comentários).
# Não há feed RSS específico de tecnologia funcional na InfoMoney.
# A classe é mantida para referência; remova o comentário e reinsira em ALL_SPIDERS
# se um feed tech funcional for disponibilizado no futuro.
class InfoMoneyTecnologiaSpider(BaseSpider):
    source_slug = "infomoney-tecnologia"
    source_name = "InfoMoney Tecnologia"
    base_url = "https://www.infomoney.com.br/tecnologia"
    feed_url = "https://www.infomoney.com.br/feed/"


class EpocaNegociosSpider(BaseSpider):
    source_slug = "epoca-negocios"
    source_name = "Época Negócios"
    base_url = "https://epocanegocios.globo.com"
    feed_url = "https://epocanegocios.globo.com/rss/ultimas/"


class EstadaoLinkSpider(BaseSpider):
    source_slug = "estadao-link"
    source_name = "Estadão Link"
    base_url = "https://www.estadao.com.br/link"
    feed_url = "https://www.estadao.com.br/arc/outboundfeeds/feeds/rss/sections/link/?outputType=xml"


class FolhaTecSpider(BaseSpider):
    source_slug = "folha-tec"
    source_name = "Folha Tec"
    base_url = "https://www1.folha.uol.com.br/tec"
    feed_url = "https://feeds.folha.uol.com.br/tec/rss091.xml"


class CnnBrasilTecnologiaSpider(BaseSpider):
    source_slug = "cnn-brasil-tecnologia"
    source_name = "CNN Brasil Tecnologia"
    base_url = "https://www.cnnbrasil.com.br/tecnologia"
    feed_url = "https://www.cnnbrasil.com.br/tecnologia/feed/"


class R7TecnologiaSpider(BaseSpider):
    source_slug = "r7-tecnologia"
    source_name = "R7 Tecnologia"
    base_url = "https://www.r7.com/tecnologia-e-ciencia"
    feed_url = "https://www.r7.com/feed/tecnologia-e-ciencia"


class TerraTecnologiaSpider(BaseSpider):
    source_slug = "terra-tecnologia"
    source_name = "Terra Tecnologia"
    base_url = "https://www.terra.com.br/byte"
    feed_url = "https://www.terra.com.br/byte/rss.xml"


# ----------------------------------------------------------------------------
ALL_SPIDERS: list[type[BaseSpider]] = [
    # Especializados
    TecMundoSpider, OlharDigitalSpider, CanaltechSpider, TecnoblogSpider,
    MeioBitSpider, GizmodoBrasilSpider, AdrenalineSpider, HardwareSpider,
    MundoConectadoSpider, ShowmetechSpider, OficinaDaNetSpider, TheBrief24Spider,
    # Generalistas (seção tech)
    # InfoMoneyTecnologiaSpider — desativada (ver comentário na classe acima)
    TiltUolSpider, TechTudoSpider, G1TecnologiaSpider, ExameTecnologiaSpider,
    EpocaNegociosSpider, EstadaoLinkSpider,
    FolhaTecSpider, CnnBrasilTecnologiaSpider, R7TecnologiaSpider,
    TerraTecnologiaSpider,
]

SPIDERS_BY_SLUG: dict[str, type[BaseSpider]] = {
    s.source_slug: s for s in ALL_SPIDERS
}
