"""
Comando: agrupa as notícias coletadas por fato (clustering cross-source).

Sem --persist: apenas imprime o relatório no terminal (modo análise).
Com --persist: cria objetos Cluster no banco e atualiza Article.cluster +
    credibility_score/credibility_label (equivale a disparar a task Celery
    manualmente, sem precisar de worker rodando).

Uso:
  python manage.py run_clustering
  python manage.py run_clustering --threshold 0.35 --window 48
  python manage.py run_clustering --limit 500 --persist
  python manage.py run_clustering --persist   (janela e limiar de settings)
"""
from django.core.management.base import BaseCommand

from apps.news.models import Article
from apps.nlp.clusterer import cluster_articles


class Command(BaseCommand):
    help = "Agrupa notícias por fato (TF-IDF + cosseno + janela temporal)."

    def add_arguments(self, parser):
        parser.add_argument("--threshold", type=float, default=None,
                            help="Limiar de similaridade de cosseno (0-1).")
        parser.add_argument("--window", type=int, default=None,
                            help="Janela temporal em horas.")
        parser.add_argument("--limit", type=int, default=None,
                            help="Usar só as N notícias mais recentes (teste).")
        parser.add_argument("--min-coverage", type=int, default=2,
                            help="Só mostra clusters com >= N fontes distintas.")
        parser.add_argument("--persist", action="store_true", default=False,
                            help="Persiste clusters no banco e recalcula credibilidade.")

    def handle(self, *args, **opts):
        from django.conf import settings

        threshold = opts["threshold"] or getattr(settings, "CLUSTERING_THRESHOLD", 0.30)
        window = opts["window"] or getattr(settings, "CLUSTERING_WINDOW_HOURS", 72)

        qs = Article.objects.select_related("source").order_by("-scraped_at")
        if opts["limit"]:
            qs = qs[:opts["limit"]]
        articles = list(qs)

        self.stdout.write(self.style.NOTICE(
            f"Agrupando {len(articles)} notícias "
            f"(limiar={threshold}, janela={window}h)..."
        ))

        result = cluster_articles(articles, threshold=threshold, window_hours=window)
        coverage = result.coverage_by_cluster()
        sizes = result.cluster_sizes()

        multi = {c: cov for c, cov in coverage.items() if cov >= 2}
        isolated = sum(1 for cov in coverage.values() if cov == 1)
        self.stdout.write(self.style.SUCCESS(
            f"\n{result.n_clusters} clusters | "
            f"{len(multi)} com 2+ fontes | {isolated} isolados"
        ))

        self.stdout.write("\nDistribuição de cobertura cross-source:")
        dist: dict[int, int] = {}
        for cov in coverage.values():
            dist[cov] = dist.get(cov, 0) + 1
        for cov in sorted(dist):
            bar = "█" * min(dist[cov], 50)
            self.stdout.write(f"  {cov:2d} fonte(s): {dist[cov]:4d} {bar}")

        min_cov = opts["min_coverage"]
        top = sorted(multi.items(), key=lambda x: -x[1])[:15]
        id2art = {a.id: a for a in articles}
        by_cluster: dict[int, list] = {}
        for lbl, aid in zip(result.labels, result.article_ids):
            by_cluster.setdefault(int(lbl), []).append(aid)

        self.stdout.write(self.style.NOTICE(
            f"\nTop clusters com >= {min_cov} fontes:"
        ))
        for cid, cov in top:
            arts = [id2art[aid] for aid in by_cluster[cid]]
            fontes = sorted({a.source.name for a in arts})
            self.stdout.write(self.style.SUCCESS(
                f"\n  ● Cluster {cid} — {cov} fontes, {len(arts)} artigos"
            ))
            self.stdout.write(f"    Fontes: {', '.join(fontes)}")
            for a in arts[:4]:
                self.stdout.write(f"      · [{a.source.name}] {a.title[:70]}")
            if len(arts) > 4:
                self.stdout.write(f"      · ... (+{len(arts)-4})")

        # --persist: salva no banco usando os artigos e o result já calculados acima.
        # NÃO chama run_clustering_task, que refaria a query com filtro de janela
        # temporal e poderia encontrar 0 artigos (artigos mais antigos que a janela).
        if opts["persist"]:
            from apps.nlp.tasks import persist_clustering
            self.stdout.write(self.style.NOTICE(
                f"\nPersistindo {len(result.article_ids)} artigos em "
                f"{result.n_clusters} clusters no banco..."
            ))
            stats = persist_clustering(result, articles)
            self.stdout.write(self.style.SUCCESS(
                f"Persistido: {stats['clusters']} clusters, "
                f"{stats['clustered']} artigos atualizados."
            ))
