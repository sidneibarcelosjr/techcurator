"""
Análise PP2: relação entre os sinais textuais de credibilidade e a
cobertura de um fato entre fontes (consenso cross-source).

Usa o campo text_signal_score (credibilidade-base, só texto, SEM o bônus
de consenso), evitando a circularidade de usar o credibility_score final.

IMPORTANTE sobre a direção: text_signal_score ALTO = texto bom (sóbrio,
com fontes); text_signal_score BAIXO = texto ruim (clickbait, oferta,
sensacionalismo). Portanto, a hipótese "texto melhor tende a ter maior
cobertura" corresponde a uma correlação POSITIVA entre text_signal_score
e cobertura.

Uso:
  python manage.py analisar_pp2
"""
from django.core.management.base import BaseCommand
from apps.news.models import Article


class Command(BaseCommand):
    help = "Analisa a relação entre sinais textuais e cobertura (PP2)."

    def handle(self, *args, **opts):
        try:
            from scipy.stats import spearmanr, mannwhitneyu
            import numpy as np
        except ImportError:
            self.stderr.write(self.style.ERROR("scipy/numpy não disponível."))
            return

        arts = list(Article.objects.select_related("cluster")
                    .exclude(cluster__isnull=True)
                    .exclude(text_signal_score__isnull=True))

        if not arts:
            self.stderr.write(self.style.ERROR(
                "Nenhuma notícia com cluster e text_signal_score. "
                "Rode 'run_clustering --persist' antes."))
            return

        coberturas = []
        texto = []     # text_signal_score: ALTO = texto bom
        for a in arts:
            cov = a.cluster.coverage if a.cluster else 1
            coberturas.append(cov)
            texto.append(float(a.text_signal_score))

        coberturas = np.array(coberturas, dtype=float)
        texto = np.array(texto, dtype=float)
        n = len(arts)

        self.stdout.write(self.style.NOTICE(
            f"\nAnálise PP2 sobre {n} notícias\n" + "=" * 52))
        self.stdout.write(
            "Nota: text_signal_score ALTO = texto sóbrio/com fontes; "
            "BAIXO = clickbait/oferta/sensacionalismo.")

        # 1) Spearman: qualidade textual x cobertura
        rho, pval = spearmanr(texto, coberturas)
        self.stdout.write("\n[1] Correlação de Spearman")
        self.stdout.write("    qualidade_textual (text_signal_score) x cobertura")
        self.stdout.write(f"    rho = {rho:.4f}")
        self.stdout.write(f"    p-valor = {pval:.3e}")
        direc = "positiva" if rho > 0 else "negativa"
        signif = "significativa" if pval < 0.05 else "não significativa"
        self.stdout.write(f"    -> correlação {direc}, {signif} ao nível de 5%")
        if rho > 0:
            self.stdout.write("    (coerente com a hipótese: texto melhor, maior cobertura)")
        else:
            self.stdout.write("    (contrário à hipótese esperada)")

        # 2) Mann-Whitney: isoladas (cov=1) vs multi-fonte (cov>=2)
        tex_iso = texto[coberturas == 1]
        tex_multi = texto[coberturas >= 2]
        self.stdout.write("\n[2] Mann-Whitney (qualidade textual)")
        self.stdout.write(f"    isoladas (cobertura=1):  {len(tex_iso):4d} notícias, "
                          f"text_signal médio = {tex_iso.mean():.4f}")
        self.stdout.write(f"    multi-fonte (cob>=2):    {len(tex_multi):4d} notícias, "
                          f"text_signal médio = {tex_multi.mean():.4f}")
        if len(tex_iso) and len(tex_multi):
            u, p2 = mannwhitneyu(tex_iso, tex_multi, alternative="two-sided")
            self.stdout.write(f"    U = {u:.1f}, p-valor = {p2:.3e}")
            signif2 = "significativa" if p2 < 0.05 else "não significativa"
            self.stdout.write(f"    -> diferença {signif2} ao nível de 5%")
            # tamanho de efeito (rank-biserial)
            rb = 1 - (2*u)/(len(tex_iso)*len(tex_multi))
            self.stdout.write(f"    tamanho de efeito (rank-biserial) = {rb:.4f}")

        # 3) text_signal médio por faixa de cobertura
        self.stdout.write("\n[3] Qualidade textual média por cobertura")
        for c in sorted(set(int(x) for x in coberturas)):
            mask = coberturas == c
            if mask.sum() >= 1:
                self.stdout.write(f"    cobertura {c:2d}: {int(mask.sum()):4d} notícias, "
                                  f"text_signal médio = {texto[mask].mean():.4f}")

        self.stdout.write("\n" + "=" * 52)
        self.stdout.write(self.style.SUCCESS("Resultado do PP2 acima."))
