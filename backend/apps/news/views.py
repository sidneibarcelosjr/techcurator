"""Views (API REST) do app news."""
from datetime import timedelta

from django.db.models import Exists, OuterRef, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Article, Category, SavedArticle, Source, Tag
from .serializers import (
    ArticleDetailSerializer,
    ArticleSerializer,
    CategorySerializer,
    SavedArticleSerializer,
    SourceSerializer,
    TagSerializer,
)


def _saved_ids_for(request):
    if request.user.is_authenticated:
        return set(
            SavedArticle.objects.filter(user=request.user)
            .values_list("article_id", flat=True)
        )
    return set()


class ArticleListView(ListAPIView):
    """Lista artigos com filtros via query string."""

    serializer_class = ArticleSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = (
            Article.objects.select_related("source", "category", "cluster")
            .prefetch_related("tags")
        )
        params = self.request.query_params

        q = params.get("q")
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(summary__icontains=q)
                | Q(content__icontains=q)
                | Q(tags__name__icontains=q)
            ).distinct()

        source = params.get("source")
        if source:
            qs = qs.filter(source__slug=source)

        category = params.get("category")
        if category:
            qs = qs.filter(category__slug=category)

        tag = params.get("tag")
        if tag:
            qs = qs.filter(tags__slug=tag)

        ordering = params.get("ordering")
        allowed = {
            "relevance_score", "-relevance_score",
            "published_at", "-published_at",
            "scraped_at", "-scraped_at",
        }
        if ordering in allowed:
            qs = qs.order_by(ordering)
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["saved_ids"] = _saved_ids_for(self.request)
        return ctx


class ArticleDetailView(RetrieveAPIView):
    queryset = (
        Article.objects.select_related("source", "category", "cluster")
        .prefetch_related("tags")
    )
    serializer_class = ArticleDetailSerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["saved_ids"] = _saved_ids_for(self.request)
        return ctx


class TrendingView(ListAPIView):
    """Top 48 das últimas 48h ordenados por relevância."""

    serializer_class = ArticleSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        since = timezone.now() - timedelta(hours=48)
        return (
            Article.objects.select_related("source", "category", "cluster")
            .prefetch_related("tags")
            .filter(Q(published_at__gte=since) | Q(scraped_at__gte=since))
            .order_by("-relevance_score", "-published_at")[:48]
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["saved_ids"] = _saved_ids_for(self.request)
        return ctx


class SourceListView(ListAPIView):
    # Só fontes ativas e com ao menos um artigo coletado (evita chips vazios
    # no filtro do front para portais desativados ou com feed quebrado).
    queryset = Source.objects.filter(
        Exists(Article.objects.filter(source=OuterRef("pk"))),
        is_active=True,
    )
    serializer_class = SourceSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class CategoryListView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None


class TagListView(ListAPIView):
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return Tag.objects.all()[:200]


class SavedArticleView(APIView):
    """GET lista salvos do usuário; POST salva um artigo."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        saved = (
            SavedArticle.objects.filter(user=request.user)
            .select_related("article", "article__source", "article__category",
                            "article__cluster")
            .prefetch_related("article__tags")
        )
        data = SavedArticleSerializer(
            saved, many=True, context={"request": request}
        ).data
        return Response(data)

    def post(self, request):
        article_id = request.data.get("article_id")
        if not article_id:
            return Response(
                {"detail": "article_id é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            article = Article.objects.get(pk=article_id)
        except Article.DoesNotExist:
            return Response(
                {"detail": "Artigo não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        obj, created = SavedArticle.objects.get_or_create(
            user=request.user, article=article
        )
        return Response(
            SavedArticleSerializer(obj, context={"request": request}).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_saved_by_article(request, article_id):
    deleted, _ = SavedArticle.objects.filter(
        user=request.user, article_id=article_id
    ).delete()
    if deleted:
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(
        {"detail": "Não estava salvo."}, status=status.HTTP_404_NOT_FOUND
    )
