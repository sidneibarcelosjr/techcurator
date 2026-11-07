"""Rotas do app news (prefixadas com /api/)."""
from django.urls import path

from . import views

urlpatterns = [
    path("articles/", views.ArticleListView.as_view(), name="article-list"),
    path("articles/trending/", views.TrendingView.as_view(), name="article-trending"),
    path("articles/<slug:slug>/", views.ArticleDetailView.as_view(), name="article-detail"),
    path("sources/", views.SourceListView.as_view(), name="source-list"),
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path("tags/", views.TagListView.as_view(), name="tag-list"),
    path("saved/", views.SavedArticleView.as_view(), name="saved-list"),
    path("saved/by-article/<int:article_id>/", views.remove_saved_by_article,
         name="saved-remove"),
]
