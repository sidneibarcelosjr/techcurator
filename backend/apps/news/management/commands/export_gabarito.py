"""
Exporta uma amostra de notícias para anotação manual do gabarito.

Uso:
  # Ver contagem por dia:
  python manage.py export_gabarito --contar

  # Exportar um dia inteiro:
  python manage.py export_gabarito --de 2026-08-03 --ate 2026-08-03

  # Exportar amostra reduzida (~N notícias), priorizando as que têm
  # potencial de agrupamento, mas mantendo uma fração de isoladas:
  python manage.py export_gabarito --de 2026-08-03 --ate 2026-08-03 --amostra 150

Gera CSV com colunas: id_noticia, fonte, data, titulo, id_grupo, e_oferta.
"""
import csv
import re
from collections import defaultdict
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db.models import Count
from django.db.models.functions import TruncDate

from apps.news.models import Article

STOP = set(
    "para com que dos das uma novo nova mais como apos pode anos brasil "
    "melhor melhores agora jogos sobre todos menos preco celular promete "
    "deixa bateria mercado agosto lanca revela confira desconto nesta segunda "
    "usuarios milhoes mundo esta este esse essa quando ainda muito".split()
)


class Command(BaseCommand):
    help = "Exporta amostra de notícias para anotação do gabarito."

    def add_arguments(self, parser):
        parser.add_argument("--contar", action="store_true")
        parser.add_argument("--de", type=str, default=None)
        parser.add_argument("--ate", type=str, default=None)
        parser.add_argument("--amostra", type=int, default=None,
                            help="Reduz para ~N notícias (seleção inteligente).")
        parser.add_argument("--saida", type=str, default="gabarito_amostra.csv")

    def handle(self, *args, **opts):
        if opts["contar"]:
            self.stdout.write("Notícias por dia (scraped_at):")
            qs = (Article.objects.annotate(dia=TruncDate("scraped_at"))
                  .values("dia").annotate(n=Count("id")).order_by("dia"))
            for r in qs:
                self.stdout.write(f"  {r['dia']}: {r['n']} notícias")
            return

        if not opts["de"] or not opts["ate"]:
            self.stderr.write(self.style.ERROR("Informe --de e --ate."))
            return

        de = datetime.strptime(opts["de"], "%Y-%m-%d").date()
        ate = datetime.strptime(opts["ate"], "%Y-%m-%d").date()

        arts = list(Article.objects.select_related("source")
                    .annotate(dia=TruncDate("scraped_at"))
                    .filter(dia__gte=de, dia__lte=ate)
                    .order_by("scraped_at"))
        total = len(arts)
        if total == 0:
            self.stderr.write(self.style.ERROR("Nenhuma notícia no intervalo."))
            return

        # Seleção inteligente (se --amostra pedido e menor que o total)
        alvo = opts["amostra"]
        if alvo and alvo < total:
            arts = self._selecionar(arts, alvo)

        saida = opts["saida"]
        with open(saida, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["id_noticia", "fonte", "data", "titulo",
                        "id_grupo", "e_oferta"])
            for a in arts:
                data_str = a.scraped_at.strftime("%d/%m") if a.scraped_at else ""
                w.writerow([a.id, a.source.name, data_str,
                            (a.title or "").strip(), "", ""])

        self.stdout.write(self.style.SUCCESS(
            f"Exportadas {len(arts)} notícias (de {total} no período) para '{saida}'."))

    def _selecionar(self, arts, alvo):
        """
        Seleciona ~alvo notícias equilibrando:
        - notícias COM potencial de agrupamento (compartilham termos marcantes);
        - uma fração (~20%) de notícias ISOLADAS (para testar casos solitários).
        """
        # mapa termo -> conjunto de fontes que o usam no título
        termo_fontes = defaultdict(set)
        art_termos = {}
        for a in arts:
            termos = {w for w in re.findall(r"\w{5,}", (a.title or "").lower())
                      if w not in STOP}
            art_termos[a.id] = termos
            for t in termos:
                termo_fontes[t].add(a.source_id)

        # termos "de agrupamento": aparecem em 2+ fontes distintas
        termos_grupo = {t for t, fs in termo_fontes.items() if len(fs) >= 2}

        com_potencial, isoladas = [], []
        for a in arts:
            if art_termos[a.id] & termos_grupo:
                com_potencial.append(a)
            else:
                isoladas.append(a)

        # ~80% com potencial, ~20% isoladas
        n_iso = max(1, int(alvo * 0.20))
        n_pot = alvo - n_iso
        sel = com_potencial[:n_pot] + isoladas[:n_iso]
        # se faltar (poucas com potencial), completa com o que sobrar
        if len(sel) < alvo:
            resto = [a for a in arts if a not in sel]
            sel += resto[:alvo - len(sel)]
        # ordena por data para a planilha ficar cronológica
        sel.sort(key=lambda a: a.scraped_at or datetime.min)
        self.stdout.write(
            f"  Seleção: {min(n_pot,len(com_potencial))} com potencial de "
            f"agrupamento + {min(n_iso,len(isoladas))} isoladas.")
        return sel