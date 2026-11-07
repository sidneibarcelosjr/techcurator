import { Bookmark, BookmarkCheck, ExternalLink } from "lucide-react";
import CredibilityBadge from "./CredibilityBadge";

function timeAgo(dateStr) {
  if (!dateStr) return "";
  const diff = (Date.now() - new Date(dateStr).getTime()) / 1000;
  if (diff < 3600) return `há ${Math.max(1, Math.floor(diff / 60))} min`;
  if (diff < 86400) return `há ${Math.floor(diff / 3600)} h`;
  const days = Math.floor(diff / 86400);
  if (days < 30) return `há ${days} d`;
  return new Date(dateStr).toLocaleDateString("pt-BR");
}

export default function NewsCard({ article, isSaved, onToggleSave, onOpen }) {
  const {
    id,
    url,
    title,
    image_url,
    tags = [],
    source,
    relevance_score,
    credibility_label,
    published_at,
  } = article;

  function handleSave(e) {
    e.preventDefault();
    e.stopPropagation();
    onToggleSave?.(id);
  }

  function handleOpen() {
    onOpen?.(article);
  }

  function onKeyDown(e) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleOpen();
    }
  }

  return (
    <article
      className="card"
      onClick={handleOpen}
      onKeyDown={onKeyDown}
      role="button"
      tabIndex={0}
      aria-label={`Abrir resumo: ${title}`}
    >
      <div className="card-media">
        {source?.name && <span className="card-source-badge">{source.name}</span>}
        {image_url ? (
          <img src={image_url} alt="" loading="lazy" />
        ) : (
          <div className="placeholder"><span className="placeholder-tc">TechCurator</span></div>
        )}
        <button
          className={`card-save${isSaved ? " saved" : ""}`}
          onClick={handleSave}
          aria-label={isSaved ? "Remover dos salvos" : "Salvar notícia"}
        >
          {isSaved ? <BookmarkCheck size={15} /> : <Bookmark size={15} />}
          {isSaved ? "Salvo" : "Salvar"}
        </button>
      </div>

      <div className="card-body">
        <h3 className="card-title">{title}</h3>

        {tags.length > 0 && (
          <div className="card-tags">
            {tags.slice(0, 4).map((t) => (
              <span className="tag" key={t.id || t.slug}>
                {t.name}
              </span>
            ))}
          </div>
        )}

        <div className="card-foot">
          <div className="card-foot-indicators">
            <CredibilityBadge label={credibility_label} compact />
            <span className="relevance-dot" title="Relevância tech">
              <i style={{ opacity: 0.35 + Math.min(relevance_score || 0, 1) * 0.65 }} />
              {Math.round((relevance_score || 0) * 100)}%
            </span>
          </div>
          <div className="card-foot-actions">
            <span className="card-foot-date">{timeAgo(published_at)}</span>
            <a
              className="open"
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
            >
              Abrir <ExternalLink size={13} />
            </a>
          </div>
        </div>
      </div>
    </article>
  );
}
