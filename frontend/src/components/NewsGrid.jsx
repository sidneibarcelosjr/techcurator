import { useState } from "react";
import NewsCard from "./NewsCard";
import ArticleModal from "./ArticleModal";

export default function NewsGrid({ articles, savedIds, onToggleSave }) {
  const [openId, setOpenId] = useState(null);

  // Resolve o artigo aberto pela lista atual, para refletir mudanças (ex.: salvar).
  const openArticle = articles.find((a) => a.id === openId) || null;
  const isOpenSaved = openArticle
    ? savedIds?.has(openArticle.id) ?? openArticle.is_saved
    : false;

  return (
    <>
      <div className="masonry">
        {articles.map((article) => (
          <NewsCard
            key={article.id}
            article={article}
            isSaved={savedIds?.has(article.id) ?? article.is_saved}
            onToggleSave={onToggleSave}
            onOpen={() => setOpenId(article.id)}
          />
        ))}
      </div>

      {openArticle && (
        <ArticleModal
          article={openArticle}
          isSaved={isOpenSaved}
          onToggleSave={onToggleSave}
          onClose={() => setOpenId(null)}
        />
      )}
    </>
  );
}
