"""
Diagnóstico: mostra ONDE o clustering automático diverge do gabarito humano.
Ajuda a entender se o ARI baixo é problema real ou artefato da métrica.

Uso:
  python manage.py diagnostico_clustering --gabarito gabarito.xlsx --limiar 0.50
"""
from collections import defaultdict

from django.core.management.base import BaseCommand
from apps.news.models import Article
from apps.nlp.clusterer import cluster_articles


class Command(BaseCommand):
    help = "Mostra divergências entre clustering e gabarito."

    def add_arguments(self, parser):
        parser.add_argument("--gabarito", type=str, required=True)
        parser.add_argument("--aba", type=str, default="Anotação")
        parser.add_argument("--limiar", type=float, default=0.50)
        parser.add_argument("--window", type=int, default=48)

    def handle(self, *args, **opts):
        import openpyxl
        wb = openpyxl.load_workbook(opts["gabarito"], data_only=True)
        ws = wb[opts["aba"]]

        header, hrow = {}, None
        for r_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            vals = [str(c).strip().lower() if c is not None else "" for c in row]
            if "id_noticia" in vals and "id_grupo" in vals:
                for c_idx, v in enumerate(vals):
                    header[v] = c_idx
                hrow = r_idx
                break
        ci_id, ci_gr = header["id_noticia"], header["id_grupo"]

        gab = {}
        for row in ws.iter_rows(min_row=hrow + 1, values_only=True):
            if ci_id >= len(row):
                continue
            rid, grp = row[ci_id], row[ci_gr] if ci_gr < len(row) else None
            if rid is None or grp is None or str(grp).strip() == "":
                continue
            try:
                gab[int(rid)] = str(grp).strip()
            except (ValueError, TypeError):
                pass

        arts = list(Article.objects.select_related("source").filter(id__in=gab.keys()))
        id2art = {a.id: a for a in arts}
        gab = {i: g for i, g in gab.items() if i in id2art}

        result = cluster_articles(arts, threshold=opts["limiar"],
                                  window_hours=opts["window"])
        auto = {aid: int(lbl) for aid, lbl in zip(result.article_ids, result.labels)}

        # grupos humanos (só os com 2+ notícias interessam para ver fusão/separação)
        gab_grupos = defaultdict(list)
        for i, g in gab.items():
            gab_grupos[g].append(i)
        gab_multi = {g: ids for g, ids in gab_grupos.items() if len(ids) >= 2}

        # grupos automáticos
        auto_grupos = defaultdict(list)
        for i in gab:
            auto_grupos[auto[i]].append(i)

        self.stdout.write(self.style.NOTICE(
            f"\n=== GRUPOS DO GABARITO HUMANO (com 2+ notícias): {len(gab_multi)} ===\n"))
        for g, ids in sorted(gab_multi.items(), key=lambda x: -len(x[1])):
            # para cada grupo humano, ver se o automático manteve junto
            auto_labels = set(auto[i] for i in ids)
            status = "JUNTOU OK" if len(auto_labels) == 1 else f"SEPAROU em {len(auto_labels)}"
            self.stdout.write(f"[Humano {g}] {len(ids)} notícias -> automático: {status}")
            for i in ids:
                self.stdout.write(f"    (auto={auto[i]}) [{id2art[i].source.name}] {id2art[i].title[:60]}")
            self.stdout.write("")

        # fusões indevidas: grupos automáticos que juntaram notícias de grupos humanos diferentes
        self.stdout.write(self.style.NOTICE(
            "\n=== FUSÕES INDEVIDAS (automático juntou o que humano separou) ===\n"))
        fusoes = 0
        for alabel, ids in auto_grupos.items():
            if len(ids) < 2:
                continue
            humanos = set(gab[i] for i in ids)
            if len(humanos) > 1:
                fusoes += 1
                self.stdout.write(f"[Auto {alabel}] juntou {len(ids)} notícias de {len(humanos)} grupos humanos:")
                for i in ids:
                    self.stdout.write(f"    (humano={gab[i]}) [{id2art[i].source.name}] {id2art[i].title[:60]}")
                self.stdout.write("")
        if fusoes == 0:
            self.stdout.write("  Nenhuma fusão indevida encontrada.")

        # resumo
        juntou_ok = sum(1 for g, ids in gab_multi.items()
                        if len(set(auto[i] for i in ids)) == 1)
        self.stdout.write(self.style.SUCCESS(
            f"\n=== RESUMO (limiar {opts['limiar']}) ===\n"
            f"Grupos humanos multi-notícia: {len(gab_multi)}\n"
            f"  Mantidos corretamente juntos pelo automático: {juntou_ok}\n"
            f"  Quebrados pelo automático: {len(gab_multi) - juntou_ok}\n"
            f"Fusões indevidas do automático: {fusoes}"))