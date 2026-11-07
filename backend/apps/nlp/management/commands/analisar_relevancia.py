"""
Diagnóstico de relevância tech: distribuição de scores na base atual,
comparação especializado vs. generalista e simulação de thresholds alternativos.

Uso básico:
  python manage.py analisar_relevancia

Com mais amostras por faixa:
  python manage.py analisar_relevancia --amostras 10

Simular impacto de thresholds específicos:
  python manage.py analisar_relevancia \\
      --simular-threshold 0.20 \\
      --simular-threshold-especializado 0.08

Exportar lista de artigos que seriam removidos:
  python manage.py analisar_relevancia \\
      --simular-threshold 0.20 \\
      --simular-threshold-especializado 0.08 \\
      --exportar /tmp/candidatos_remocao.tsv
"""
from collections import defaultdict

from django.core.management.base import BaseCommand

from apps.news.models import Article


class Command(BaseCommand):
    help = "Distribui artigos por faixa de relevance_score e simula impacto de thresholds."

    def add_arguments(self, parser):
        parser.add_argument(
            "--amostras", type=int, default=5,
            help="Títulos exibidos por faixa (padrão: 5).",
        )
        parser.add_argument(
            "--simular-threshold", type=float, default=None, dest="sim_gen",
            help="Threshold para fontes generalistas a simular (ex.: 0.20).",
        )
        parser.add_argument(
            "--simular-threshold-especializado", type=float, default=None,
            dest="sim_esp",
            help="Threshold para fontes is_tech_specialized=True (ex.: 0.08).",
        )
        parser.add_argument(
            "--exportar", type=str, default=None,
            help="Salva artigos que seriam removidos em arquivo .tsv (sem deletar).",
        )

    def handle(self, *args, **opts):
        amostras = opts["amostras"]
        sim_gen = opts["sim_gen"]
        sim_esp = opts["sim_esp"]
        exportar = opts["exportar"]

        articles = list(
            Article.objects
            .select_related("source")
            .only("id", "title", "relevance_score",
                  "source__name", "source__is_tech_specialized")
            .order_by("relevance_score")
        )
        total = len(articles)

        if total == 0:
            self.stdout.write(self.style.WARNING("Nenhum artigo na base."))
            return

        # Faixas de 0.1
        BUCKETS = [f"{i/10:.1f}–{(i+1)/10:.1f}" for i in range(10)]
        buckets: dict[str, list] = defaultdict(list)
        for a in articles:
            idx = min(int(a.relevance_score * 10), 9)
            buckets[BUCKETS[idx]].append(a)

        n_esp = sum(1 for a in articles if a.source.is_tech_specialized)
        n_gen = total - n_esp

        # ------------------------------------------------------------------ #
        #  CABEÇALHO                                                          #
        # ------------------------------------------------------------------ #
        self.stdout.write("")
        self._linha("=")
        self.stdout.write(
            self.style.MIGRATE_HEADING(f"  DIAGNÓSTICO DE RELEVÂNCIA — {total} artigos")
        )
        self._linha("=")
        self.stdout.write("")

        self.stdout.write(
            f"  Especializados  (is_tech_specialized=True) : "
            f"{n_esp:>5}  ({n_esp/total*100:.1f}%)"
        )
        self.stdout.write(
            f"  Generalistas    (is_tech_specialized=False): "
            f"{n_gen:>5}  ({n_gen/total*100:.1f}%)"
        )
        self.stdout.write("")

        # ------------------------------------------------------------------ #
        #  HISTOGRAMA                                                          #
        # ------------------------------------------------------------------ #
        self._secao("HISTOGRAMA POR FAIXA DE relevance_score")
        self.stdout.write(
            f"  {'Faixa':>8}  {'Total':>6}  {'Esp.':>6}  {'Gen.':>6}  Barra (% do total)"
        )
        self._linha("-")

        for label in BUCKETS:
            group = buckets.get(label, [])
            if not group:
                continue
            n = len(group)
            n_s = sum(1 for a in group if a.source.is_tech_specialized)
            n_g = n - n_s
            bar = "█" * max(1, int(n / total * 40))
            self.stdout.write(
                f"  {label:>8}  {n:>6}  {n_s:>6}  {n_g:>6}  {bar}"
            )

        self._linha("-")
        self.stdout.write(f"  {'TOTAL':>8}  {total:>6}\n")

        # ------------------------------------------------------------------ #
        #  AMOSTRAS POR FAIXA                                                 #
        # ------------------------------------------------------------------ #
        self._secao(f"AMOSTRAS DE TÍTULOS POR FAIXA (até {amostras} por faixa)")
        self.stdout.write(
            "  [ESP]=especializado  [GEN]=generalista  score=relevance_score\n"
        )
        for label in BUCKETS:
            group = buckets.get(label, [])
            if not group:
                continue
            self.stdout.write(
                self.style.WARNING(f"  ── {label} ──  ({len(group)} artigos)")
            )
            for a in group[:amostras]:
                tipo = "ESP" if a.source.is_tech_specialized else "GEN"
                self.stdout.write(
                    f"    [{tipo}] {a.relevance_score:.3f}  "
                    f"{a.source.name:<22} {a.title[:60]}"
                )
            self.stdout.write("")

        # ------------------------------------------------------------------ #
        #  SIMULAÇÃO DE THRESHOLDS                                            #
        # ------------------------------------------------------------------ #
        if sim_gen is not None or sim_esp is not None:
            t_g = sim_gen if sim_gen is not None else 0.15
            t_e = sim_esp if sim_esp is not None else 0.00
            self._detalhar_simulacao(articles, t_g, t_e, exportar)
        else:
            self._tabela_cenarios(articles, total)

        self.stdout.write("")

    # ---------------------------------------------------------------------- #
    #  HELPERS                                                                #
    # ---------------------------------------------------------------------- #

    def _secao(self, titulo: str):
        self.stdout.write(self.style.MIGRATE_LABEL(titulo))

    def _linha(self, char: str = "-", largura: int = 64):
        self.stdout.write(char * largura)

    def _tabela_cenarios(self, articles: list, total: int):
        """Tabela rápida com quatro cenários pré-definidos."""
        self._secao("SIMULAÇÃO RÁPIDA — impacto de thresholds alternativos na base atual")
        self.stdout.write(
            "  Cenário                                          Mantém    Remove"
        )
        self._linha("-", 72)

        scenarios = [
            ("Atual      (bypass esp. total  + gen≥0.15)", None,  0.15),
            ("Seguro     (esp≥0.05 + gen≥0.15)",          0.05,  0.15),
            ("Moderado   (esp≥0.08 + gen≥0.20)",          0.08,  0.20),
            ("Rigoroso   (esp≥0.10 + gen≥0.25)",          0.10,  0.25),
        ]

        for name, t_e, t_g in scenarios:
            kept = sum(
                1 for a in articles
                if (a.source.is_tech_specialized
                    and (t_e is None or a.relevance_score >= t_e))
                or (not a.source.is_tech_specialized
                    and a.relevance_score >= t_g)
            )
            removed = total - kept
            self.stdout.write(
                f"  {name:<48}  {kept:>5} ({kept/total*100:.1f}%)  {removed:>5}"
            )

        self.stdout.write("")
        self.stdout.write(
            "  Para ver os títulos que seriam removidos, use:\n"
            "    --simular-threshold 0.20 --simular-threshold-especializado 0.08\n"
            "  Para exportar a lista sem deletar:\n"
            "    ... --exportar /tmp/candidatos_remocao.tsv"
        )

    def _detalhar_simulacao(self, articles, t_gen, t_esp, exportar_path):
        """Mostra (e opcionalmente exporta) artigos que seriam removidos."""
        to_remove = []
        for a in articles:
            if a.source.is_tech_specialized:
                if a.relevance_score < t_esp:
                    to_remove.append(a)
            else:
                if a.relevance_score < t_gen:
                    to_remove.append(a)

        total = len(articles)
        self._secao(
            f"SIMULAÇÃO DETALHADA: esp≥{t_esp:.2f}  +  gen≥{t_gen:.2f}"
        )
        self.stdout.write(
            f"  Seriam removidos: {len(to_remove)} de {total} artigos "
            f"({len(to_remove)/total*100:.1f}%)"
        )
        self.stdout.write(
            f"  Seriam mantidos : {total - len(to_remove)} artigos "
            f"({(total-len(to_remove))/total*100:.1f}%)"
        )
        self.stdout.write(
            self.style.WARNING(
                "  NENHUM artigo foi deletado — esta é apenas uma projeção."
            )
        )
        self.stdout.write("")

        if not to_remove:
            self.stdout.write("  Nenhum artigo removido com esses thresholds.")
            return

        # Mostrar por tipo de fonte para facilitar a decisão
        esp_removidos = [a for a in to_remove if a.source.is_tech_specialized]
        gen_removidos = [a for a in to_remove if not a.source.is_tech_specialized]

        if esp_removidos:
            self.stdout.write(
                f"  De fontes ESPECIALIZADAS (score < {t_esp:.2f}): "
                f"{len(esp_removidos)} artigos"
            )
            for a in esp_removidos[:30]:
                self.stdout.write(
                    f"    [{a.id:>6}] {a.relevance_score:.3f}  "
                    f"{a.source.name:<22}  {a.title[:55]}"
                )
            if len(esp_removidos) > 30:
                self.stdout.write(f"    ... e mais {len(esp_removidos)-30}.")
            self.stdout.write("")

        if gen_removidos:
            self.stdout.write(
                f"  De fontes GENERALISTAS (score < {t_gen:.2f}): "
                f"{len(gen_removidos)} artigos"
            )
            for a in gen_removidos[:30]:
                self.stdout.write(
                    f"    [{a.id:>6}] {a.relevance_score:.3f}  "
                    f"{a.source.name:<22}  {a.title[:55]}"
                )
            if len(gen_removidos) > 30:
                self.stdout.write(f"    ... e mais {len(gen_removidos)-30}.")
            self.stdout.write("")

        if exportar_path:
            with open(exportar_path, "w", encoding="utf-8") as f:
                f.write(
                    f"# Simulação: esp>={t_esp:.2f} + gen>={t_gen:.2f}\n"
                    f"# {len(to_remove)} artigos seriam removidos (NÃO foram deletados)\n"
                    f"# Colunas: id | score | tipo | fonte | título\n\n"
                )
                for a in to_remove:
                    tipo = "ESP" if a.source.is_tech_specialized else "GEN"
                    f.write(
                        f"{a.id}\t{a.relevance_score:.4f}\t{tipo}\t"
                        f"{a.source.name}\t{a.title}\n"
                    )
            self.stdout.write(
                self.style.SUCCESS(f"  Lista exportada para: {exportar_path}")
            )
