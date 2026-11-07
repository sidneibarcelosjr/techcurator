"""Modelos de dados do TechCurator."""
from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify


class Cluster(models.Model):
    """
    Agrupamento de notícias que cobrem o mesmo fato (clustering cross-source).

    Um Cluster é recriado a cada execução da tarefa periódica de clustering.
    'coverage' = nº de fontes distintas que cobrem o fato.
    'size'     = nº de artigos no cluster.
    """

    coverage = models.IntegerField(default=1)
    size = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-coverage", "-size"]

    def __str__(self) -> str:
        return f"Cluster #{self.id} ({self.coverage} fontes, {self.size} artigos)"


class Source(models.Model):
    """Portal de notícias (fonte de scraping)."""

    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    base_url = models.URLField(blank=True)
    feed_url = models.URLField(blank=True)
    # Portais 100% especializados em tech são "confiáveis": dispensam o limiar.
    is_tech_specialized = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Category(models.Model):
    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=120)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    slug = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:100]
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Article(models.Model):
    """Notícia coletada e enriquecida pelo pipeline de NLP."""

    source = models.ForeignKey(Source, on_delete=models.CASCADE,
                               related_name="articles")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name="articles")
    tags = models.ManyToManyField(Tag, blank=True, related_name="articles")
    cluster = models.ForeignKey(Cluster, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name="articles")

    title = models.CharField(max_length=400)
    slug = models.SlugField(max_length=255, unique=True)
    url = models.URLField(max_length=1000)
    image_url = models.URLField(max_length=1000, blank=True)

    content = models.TextField(blank=True)
    summary = models.TextField(blank=True)

    relevance_score = models.FloatField(default=0.0, db_index=True)
    summarizer_method = models.CharField(max_length=30, default="luhn")
    dedup_hash = models.CharField(max_length=64, unique=True, db_index=True)

    # Credibilidade: score em [0,1] e faixa textual ("high"/"medium"/"low").
    # Calculado pelo pipeline na coleta (texto) e refinado pela tarefa de
    # clustering (adiciona o componente de consenso cross-source).
    credibility_score = models.FloatField(null=True, blank=True)
    credibility_label = models.CharField(max_length=10, blank=True)
    # Credibilidade-base textual (text_credibility_score), SEM o bônus de
    # consenso. Exposta separadamente para análise estatística (evita
    # circularidade ao correlacionar sinais textuais com cobertura).
    text_signal_score = models.FloatField(null=True, blank=True)

    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    scraped_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-published_at", "-scraped_at"]
        indexes = [
            models.Index(fields=["-relevance_score"]),
            models.Index(fields=["-published_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "artigo"
            slug = base
            i = 2
            while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title


class SavedArticle(models.Model):
    """Vínculo usuário ↔ artigo salvo para leitura posterior."""

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="saved_articles")
    article = models.ForeignKey(Article, on_delete=models.CASCADE,
                                related_name="saved_by")
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "article")
        ordering = ["-saved_at"]

    def __str__(self) -> str:
        return f"{self.user.username} → {self.article.title[:40]}"
