"""
Avalia o clustering automático contra o gabarito humano (PP1).

Lê a anotação humana de uma planilha .xlsx (colunas: id_noticia, id_grupo),
roda o clustering SOBRE AS MESMAS notícias do gabarito em vários limiares,
e calcula o ARI (Adjusted Rand Index) de cada limiar contra o gabarito.

Uso:
  python manage.py avaliar_clustering --gabarito gabarito_amostra.xlsx
  python manage.py avaliar_clustering --gabarito gab.xlsx --limiares 0.35 0.40 0.42 0.45 0.50
  python manage.py avaliar_clustering --gabarito gab.xlsx --sem-ofertas

Requer: openpyxl, scikit-learn, scipy (já usados no projeto).
"""
from django.core.management.base import BaseCommand
from sklearn.metrics import adjusted_rand_score, v_measure_score

from apps.news.models import Article
# ajuste este import conforme onde você colocou o clusterer.py:
from apps.nlp.clusterer import cluster_articles


class Command(BaseCommand):
    help = "Avalia o clustering contra o gabarito humano (ARI por limiar)."

    def add_arguments(self, parser):
        parser.add_argument("--gabarito", type=str, required=True,
                            help="Caminho do .xlsx com colunas id_noticia, id_grupo.")
        parser.add_argument("--aba", type=str, default="Anotação",
                            help="Nome da aba da planilha (padrão: Anotação).")
        parser.add_argument("--limiares", type=float, nargs="+",
                            default=[0.35, 0.40, 0.42, 0.45, 0.50],
                            help="Limiares a testar.")
        parser.add_argument("--window", type=int, default=48,
                            help="Janela temporal em horas.")
        parser.add_argument("--sem-ofertas", action="store_true",
                            help="Exclui notícias marcadas como oferta (col. e_oferta).")

    def handle(self, *args, **opts):
        try:
            import openpyxl
        except ImportError:
            self.stderr.write(self.style.ERROR(
                "openpyxl não instalado. Rode: pip install openpyxl"))
            return

        # 1) Ler o gabarito da planilha
        wb = openpyxl.load_workbook(opts["gabarito"], data_only=True)
        aba = opts["aba"]
        if aba not in wb.sheetnames:
            self.stderr.write(self.style.ERROR(
                f"Aba '{aba}' não encontrada. Abas: {wb.sheetnames}"))
            return
        ws = wb[aba]

        # localizar colunas pelo cabeçalho
        header = {}
        header_row = None
        for r_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            vals = [str(c).strip().lower() if c is not None else "" for c in row]
            if "id_noticia" in vals and "id_grupo" in vals:
                for c_idx, v in enumerate(vals):
                    header[v] = c_idx
                header_row = r_idx
                break
        if header_row is None:
            self.stderr.write(self.style.ERROR(
                "Não achei o cabeçalho com 'id_noticia' e 'id_grupo'."))
            return

        ci_id = header["id_noticia"]
        ci_gr = header["id_grupo"]
        ci_of = header.get("e_oferta")

        gabarito = {}   # id_noticia -> id_grupo (humano)
        ofertas = set()
        for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
            if ci_id >= len(row):
                continue
            rid = row[ci_id]
            grp = row[ci_gr] if ci_gr < len(row) else None
            if rid is None or grp is None or str(grp).strip() == "":
                continue
            try:
                rid = int(rid)
            except (ValueError, TypeError):
                continue
            gabarito[rid] = str(grp).strip()
            if ci_of is not None and ci_of < len(row):
                of = row[ci_of]
                if of and str(of).strip().lower() in ("sim", "s", "1", "true"):
                    ofertas.add(rid)

        if opts["sem_ofertas"]:
            for rid in ofertas:
                gabarito.pop(rid, None)

        n_gab = len(gabarito)
        n_grupos = len(set(gabarito.values()))
        self.stdout.write(self.style.NOTICE(
            f"Gabarito: {n_gab} notícias anotadas, {n_grupos} grupos "
            f"({'sem' if opts['sem_ofertas'] else 'com'} ofertas)."))
        if opts["sem_ofertas"]:
            self.stdout.write(f"  ({len(ofertas)} ofertas excluídas)")

        # 2) Carregar as notícias correspondentes
        arts = list(Article.objects.select_related("source")
                    .filter(id__in=gabarito.keys()))
        achadas = {a.id for a in arts}
        faltando = set(gabarito.keys()) - achadas
        if faltando:
            self.stdout.write(self.style.WARNING(
                f"  Atenção: {len(faltando)} ids do gabarito não achados no banco."))
            for rid in faltando:
                gabarito.pop(rid, None)

        # 3) Para cada limiar, rodar clustering e calcular ARI
        self.stdout.write("\n" + "=" * 52)
        self.stdout.write(f"{'Limiar':>8} | {'ARI':>7} | {'V-measure':>9} | {'clusters':>8}")
        self.stdout.write("=" * 52)

        melhor = (None, -1)
        for tau in opts["limiares"]:
            result = cluster_articles(arts, threshold=tau,
                                      window_hours=opts["window"])
            # alinhar rótulos humano x automático na mesma ordem
            auto = {aid: int(lbl) for aid, lbl in
                    zip(result.article_ids, result.labels)}
            ids = [a.id for a in arts if a.id in gabarito]
            y_true = [gabarito[i] for i in ids]
            y_pred = [auto[i] for i in ids]

            ari = adjusted_rand_score(y_true, y_pred)
            vms = v_measure_score(y_true, y_pred)
            self.stdout.write(
                f"{tau:>8.2f} | {ari:>7.3f} | {vms:>9.3f} | {result.n_clusters:>8}")
            if ari > melhor[1]:
                melhor = (tau, ari)

        self.stdout.write("=" * 52)
        self.stdout.write(self.style.SUCCESS(
            f"\nMelhor limiar: {melhor[0]:.2f} (ARI = {melhor[1]:.3f})"))
        self.stdout.write(
            "\nEste é o resultado do PP1: o limiar que maximiza a concordância\n"
            "entre o clustering automático e o seu gabarito humano.")