import { useEffect } from "react";
import { Bookmark, BookmarkCheck, ExternalLink, X } from "lucide-react";
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

function coverageText(coverage) {
  if (!coverage || coverage <= 1) return "Notícia isolada (1 fonte)";
  return `Coberta por ${coverage} fonte${coverage > 1 ? "s" : ""} distintas`;
}

export default function ArticleModal({ article, isSaved, onToggleSave, onClose }) {
  useEffect(() => {
    function onKey(e) {
      if (e.key === "Escape") onClose?.();
    }
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  if (!article) return null;

  const {
    id, title, url, image_url, summary, tags = [], source,
    relevance_score, published_at, credibility_label, credibility_score,
    cluster_coverage,
  } = article;

  return (
    <div className="modal-overlay" onClick={onClose} role="presentation">
      <div
        className="modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <button className="modal-close" onClick={onClose} aria-label="Fechar">
          <X size={18} />
        </button>

        <div className="modal-media">
          {source?.name && (
            <span className="card-source-badge">{source.name}</span>
          )}
          {image_url ? (
            <img src={image_url} alt="" />
          ) : (
            <div className="placeholder"><span className="placeholder-tc">TechCurator</span></div>
          )}
        </div>

        <div className="modal-body">
          <div className="modal-meta">
            <span className="relevance-dot" title="Relevância tech">
              <i style={{ opacity: 0.35 + Math.min(relevance_score || 0, 1) * 0.65 }} />
              {Math.round((relevance_score || 0) * 100)}%
            </span>
            <span>{timeAgo(published_at)}</span>
          </div>

          <h2 className="modal-title">{title}</h2>

          {/* Bloco de credibilidade */}
          {credibility_label && (
            <div className="cred-block">
              <div className="cred-block-head">
                <CredibilityBadge label={credibility_label} />
                {credibility_score != null && (
                  <span className="cred-score">
                    {Math.round(credibility_score * 100)}
                    <span className="cred-score-max">/100</span>
                  </span>
                )}
              </div>
              <p className="cred-explain">
                {coverageText(cluster_coverage)} ·{" "}
                Estimativa baseada em consenso entre fontes e sinais textuais.
                Não é um veredito de verdadeiro/falso.
              </p>
            </div>
          )}

          {/* Resumo extrativo (Luhn) */}
          {summary && (
            <div className="modal-summary">
              <p>{summary}</p>
            </div>
          )}

          {tags.length > 0 && (
            <div className="card-tags modal-tags">
              {tags.slice(0, 8).map((t) => (
                <span className="tag" key={t.id || t.slug}>
                  {t.name}
                </span>
              ))}
            </div>
          )}

          <div className="modal-actions">
            <button
              className={`btn${isSaved ? " btn-primary" : ""}`}
              onClick={() => onToggleSave?.(id)}
            >
              {isSaved ? <BookmarkCheck size={16} /> : <Bookmark size={16} />}
              {isSaved ? "Salvo" : "Salvar"}
            </button>

            <a
              className="btn btn-primary"
              href={url}
              target="_blank"
              rel="noopener noreferrer"
            >
              Ler matéria completa <ExternalLink size={15} />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
