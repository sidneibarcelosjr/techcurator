import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import FilterBar from "../components/FilterBar";
import NewsGrid from "../components/NewsGrid";
import { newsApi } from "../services/api";
import { useSavedArticles } from "../hooks/useSavedArticles";
import { useAuth } from "../context/AuthContext";

export default function Home({ onNeedAuth }) {
  const [params, setParams] = useSearchParams();
  const { isAuthenticated } = useAuth();
  const { savedIds, toggle } = useSavedArticles();

  const [articles, setArticles] = useState([]);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const q = params.get("q") || "";
  const source = params.get("source") || "";
  const category = params.get("category") || "";

  const sentinel = useRef(null);

  const load = useCallback(
    async (pageNum, replace) => {
      setLoading(true);
      setError(false);
      try {
        const data = await newsApi.articles({
          q: q || undefined,
          source: source || undefined,
          category: category || undefined,
          ordering: "-published_at",
          page: pageNum,
        });
        setHasNext(Boolean(data.next));
        setArticles((prev) => (replace ? data.results : [...prev, ...data.results]));
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    },
    [q, source, category]
  );

  // Recarrega do zero quando os filtros mudam.
  useEffect(() => {
    setPage(1);
    load(1, true);
  }, [load]);

  // Infinite scroll.
  useEffect(() => {
    if (!sentinel.current) return;
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNext && !loading) {
          const next = page + 1;
          setPage(next);
          load(next, false);
        }
      },
      { rootMargin: "600px" }
    );
    obs.observe(sentinel.current);
    return () => obs.disconnect();
  }, [hasNext, loading, page, load]);

  function updateFilters(patch) {
    const next = new URLSearchParams(params);
    Object.entries(patch).forEach(([k, v]) => {
      v ? next.set(k, v) : next.delete(k);
    });
    setParams(next);
  }

  function handleToggle(id) {
    if (!isAuthenticated) return onNeedAuth?.();
    toggle(id);
  }

  return (
    <div className="container page">
      <div className="page-head">
        <h1>{q ? `Resultados para “${q}”` : "Curadoria de tecnologia"}</h1>
        <p>
          {q
            ? "Notícias que correspondem à sua busca."
            : "Notícias coletadas de 23 portais, resumidas e classificadas automaticamente."}
        </p>
        <div className="accent-rule" />
      </div>

      <FilterBar source={source} category={category} onChange={updateFilters} />

      {error && (
        <div className="center-state">
          <h2>Não foi possível carregar</h2>
          <p>Verifique se o backend está rodando e se o scraping já foi executado.</p>
        </div>
      )}

      {!error && articles.length === 0 && !loading && (
        <div className="center-state">
          <h2>Nenhuma notícia ainda</h2>
          <p>Rode o scraping no backend para popular o feed.</p>
        </div>
      )}

      <NewsGrid articles={articles} savedIds={savedIds} onToggleSave={handleToggle} />

      {loading && <div className="spinner" aria-label="Carregando" />}
      <div ref={sentinel} className="sentinel" />
    </div>
  );
}
