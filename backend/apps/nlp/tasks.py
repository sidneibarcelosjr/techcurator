"""
Tarefas Celery do módulo NLP.

run_clustering_task — reclusteriza notícias da janela recente, persiste os
    agrupamentos e recalcula a credibilidade com o componente de consenso.
    Deve ser agendada via Celery Beat (Admin → Periodic Tasks).

persist_clustering — função pura de persistência reutilizada pelo comando
    de management `run_clustering --persist` e pela task Celery. Recebe o
    ClusterResult já calculado e a lista de artigos correspondente, evitando
    que a persistência refaça a query com uma janela temporal diferente da
    usada no cálculo (o que causava "0 artigos atualizados").
"""
from __future__ import annotations

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


def persist_clustering(result, articles) -> dict:
    """
    Persiste um ClusterResult no banco e recalcula credibilidade.

    Recebe o resultado já calculado e a lista de artigos usada no cálculo —
    não refaz query nem reaplica filtro temporal, garantindo que persiste
    exatamente o que foi mostrado no terminal.

    Passos:
      1. Coleta IDs dos Cluster anteriores desses artigos (para limpeza).
      2. Cria novos objetos Cluster (um por label distinto).
      3. Para cada artigo: atualiza cluster FK e recalcula credibility.
      4. Apaga Clusters anteriores que ficaram sem artigos (orphans).
    """
    from apps.news.models import Article, Cluster
    from apps.nlp.credibility import compute_credibility, text_credibility_score

    if not result.article_ids:
        logger.info("persist_clustering: resultado vazio, nada a persistir.")
        return {"clustered": 0, "clusters": 0}

    art_id_set = set(result.article_ids)
    logger.info("persist_clustering: %d artigos, %d labels únicos.",
                len(art_id_set), len({int(l) for l in result.labels}))

    # 1. Captura clusters anteriores ANTES de criar os novos.
    old_cluster_ids = set(
        Article.objects.filter(pk__in=art_id_set, cluster__isnull=False)
        .values_list("cluster_id", flat=True)
    )
    logger.info("persist_clustering: %d clusters anteriores encontrados para limpeza.",
                len(old_cluster_ids))

    coverage_map = result.coverage_by_cluster()
    size_map = result.cluster_sizes()

    # 2. Cria novos Clusters.
    new_cluster_map: dict[int, Cluster] = {}
    for lbl_id in {int(lbl) for lbl in result.labels}:
        new_cluster_map[lbl_id] = Cluster.objects.create(
            coverage=coverage_map.get(lbl_id, 1),
            size=size_map.get(lbl_id, 1),
        )
    logger.info("persist_clustering: %d novos Cluster criados.", len(new_cluster_map))

    # 3. Atualiza artigos: usa o dict em memória para evitar N queries individuais.
    art_dict = {a.id: a for a in articles}
    updated = 0
    skipped = 0
    for lbl, art_id in zip(result.labels, result.article_ids):
        cluster_obj = new_cluster_map[int(lbl)]
        art = art_dict.get(art_id)
        if art is None:
            logger.warning("persist_clustering: artigo id=%d não encontrado em memória, pulando.", art_id)
            skipped += 1
            continue
        score, label = compute_credibility(
            title=art.title or "",
            content=art.content or "",
            coverage=cluster_obj.coverage,
        )
        Article.objects.filter(pk=art_id).update(
            cluster=cluster_obj,
            credibility_score=score,
            credibility_label=label,
            text_signal_score=round(
                text_credibility_score(art.title or "", art.content or ""), 4
            ),
        )
        updated += 1

    if skipped:
        logger.warning("persist_clustering: %d artigos pulados (não encontrados).", skipped)

    # 4. Remove Clusters anteriores que ficaram sem artigos (orphans).
    if old_cluster_ids:
        orphan_ids = [
            cid for cid in old_cluster_ids
            if not Article.objects.filter(cluster_id=cid).exists()
        ]
        if orphan_ids:
            Cluster.objects.filter(id__in=orphan_ids).delete()
            logger.info("persist_clustering: %d clusters orphans removidos.", len(orphan_ids))

    logger.info("persist_clustering concluído: %d clusters criados, %d artigos atualizados.",
                len(new_cluster_map), updated)
    return {"clustered": updated, "clusters": len(new_cluster_map)}


@shared_task(name="nlp.run_clustering_and_credibility")
def run_clustering_task(
    window_hours: int | None = None,
    threshold: float | None = None,
    min_df: int = 2,
) -> dict:
    """
    Reclusteriza as notícias da janela recente e atualiza credibilidade.

    Busca artigos, calcula clustering e delega persistência a
    persist_clustering() — a mesma função usada pelo comando de management.

    Parâmetros podem ser passados ao invocar a task manualmente:
        from apps.nlp.tasks import run_clustering_task
        run_clustering_task.delay(window_hours=48, threshold=0.35)
    """
    from django.conf import settings

    from apps.nlp.clusterer import cluster_articles

    if window_hours is None:
        window_hours = getattr(settings, "CLUSTERING_WINDOW_HOURS", 72)
    if threshold is None:
        threshold = getattr(settings, "CLUSTERING_THRESHOLD", 0.30)

    from apps.news.models import Article
    since = timezone.now() - timedelta(hours=window_hours)
    articles = list(
        Article.objects.select_related("source")
        .filter(scraped_at__gte=since)
        .order_by("-scraped_at")
    )

    if not articles:
        logger.info("run_clustering_task: nenhum artigo na janela de %dh.", window_hours)
        return {"clustered": 0, "clusters": 0}

    logger.info("run_clustering_task: clusterizando %d artigos (janela=%dh, limiar=%.2f)...",
                len(articles), window_hours, threshold)

    result = cluster_articles(
        articles,
        threshold=threshold,
        window_hours=window_hours,
        min_df=min_df,
    )

    return persist_clustering(result, articles)
