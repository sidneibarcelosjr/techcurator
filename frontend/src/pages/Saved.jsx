import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import NewsGrid from "../components/NewsGrid";
import { savedApi } from "../services/api";
import { useSavedArticles } from "../hooks/useSavedArticles";

export default function Saved() {
  const { savedIds, toggle } = useSavedArticles();
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  async function fetchSaved() {
    setLoading(true);
    try {
      const items = await savedApi.list();
      setArticles(items.map((s) => s.article));
    } catch {
      setArticles([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchSaved();
  }, []);

  function handleToggle(id) {
    toggle(id);
    // Remove imediatamente da lista visível.
    setArticles((prev) => prev.filter((a) => a.id !== id));
  }

  return (
    <div className="container page">
      <div className="page-head">
        <h1>Suas notícias salvas</h1>
        <p>Tudo que você guardou para ler depois.</p>
        <div className="accent-rule" />
      </div>

      {loading && <div className="spinner" aria-label="Carregando" />}

      {!loading && articles.length === 0 && (
        <div className="center-state">
          <h2>Nada salvo por aqui</h2>
          <p>
            Passe o mouse sobre um card e toque em <strong>Salvar</strong>.{" "}
            <Link to="/" style={{ color: "var(--accent-ink)", fontWeight: 600 }}>
              Explorar o feed
            </Link>
          </p>
        </div>
      )}

      <NewsGrid articles={articles} savedIds={savedIds} onToggleSave={handleToggle} />
    </div>
  );
}
