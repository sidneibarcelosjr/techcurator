from django.contrib import admin

from .models import Article, Category, Cluster, SavedArticle, Source, Tag


@admin.register(Cluster)
class ClusterAdmin(admin.ModelAdmin):
    list_display = ("id", "coverage", "size", "created_at")
    list_filter = ("coverage",)
    ordering = ("-created_at",)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_tech_specialized", "is_active")
    list_filter = ("is_tech_specialized", "is_active")
    search_fields = ("name", "slug")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "relevance_score", "credibility_label",
                    "credibility_score", "cluster", "published_at")
    list_filter = ("source", "credibility_label", "category")
    search_fields = ("title", "summary")
    date_hierarchy = "published_at"
    raw_id_fields = ("cluster",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)


@admin.register(SavedArticle)
class SavedArticleAdmin(admin.ModelAdmin):
    list_display = ("user", "article", "saved_at")
