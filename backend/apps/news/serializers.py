"""Serializers do app news."""
from rest_framework import serializers

from .models import Article, Category, SavedArticle, Source, Tag


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ["id", "slug", "name", "base_url", "is_tech_specialized"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "slug", "name"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "slug", "name"]


class ArticleSerializer(serializers.ModelSerializer):
    source = SourceSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    is_saved = serializers.SerializerMethodField()
    cluster_coverage = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "id", "title", "slug", "url", "image_url", "summary",
            "relevance_score", "summarizer_method",
            "credibility_score", "credibility_label", "cluster_coverage",
            "published_at", "scraped_at",
            "source", "category", "tags", "is_saved",
        ]

    def get_is_saved(self, obj) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        saved_ids = self.context.get("saved_ids")
        if saved_ids is not None:
            return obj.id in saved_ids
        return SavedArticle.objects.filter(
            user=request.user, article=obj
        ).exists()

    def get_cluster_coverage(self, obj) -> int | None:
        """Número de fontes distintas no cluster deste artigo (ou None)."""
        if obj.cluster_id is None:
            return None
        return obj.cluster.coverage


class ArticleDetailSerializer(ArticleSerializer):
    class Meta(ArticleSerializer.Meta):
        fields = ArticleSerializer.Meta.fields + ["content"]


class SavedArticleSerializer(serializers.ModelSerializer):
    article = ArticleSerializer(read_only=True)

    class Meta:
        model = SavedArticle
        fields = ["id", "article", "saved_at"]
