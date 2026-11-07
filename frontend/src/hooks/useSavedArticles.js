import { useCallback, useEffect, useState } from "react";
import { savedApi } from "../services/api";
import { useAuth } from "../context/AuthContext";

/**
 * Mantém o conjunto de IDs de artigos salvos do usuário e expõe toggle.
 */
export function useSavedArticles() {
  const { isAuthenticated } = useAuth();
  const [savedIds, setSavedIds] = useState(() => new Set());
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    if (!isAuthenticated) {
      setSavedIds(new Set());
      return;
    }
    setLoading(true);
    try {
      const items = await savedApi.list();
      setSavedIds(new Set(items.map((s) => s.article.id)));
    } catch {
      /* silencioso */
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const toggle = useCallback(
    async (articleId) => {
      const isSaved = savedIds.has(articleId);
      // Atualização otimista.
      setSavedIds((prev) => {
        const next = new Set(prev);
        isSaved ? next.delete(articleId) : next.add(articleId);
        return next;
      });
      try {
        if (isSaved) await savedApi.remove(articleId);
        else await savedApi.save(articleId);
      } catch {
        // Reverte em caso de erro.
        setSavedIds((prev) => {
          const next = new Set(prev);
          isSaved ? next.add(articleId) : next.delete(articleId);
          return next;
        });
      }
    },
    [savedIds]
  );

  return { savedIds, toggle, refresh, loading };
}
