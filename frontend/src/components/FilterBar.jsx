import { useEffect, useState } from "react";
import { newsApi } from "../services/api";

export default function FilterBar({ source, category, onChange }) {
  const [sources, setSources] = useState([]);
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    newsApi.sources().then(setSources).catch(() => {});
    newsApi.categories().then(setCategories).catch(() => {});
  }, []);

  function pick(key, value) {
    onChange({ [key]: value === current(key) ? "" : value });
  }
  function current(key) {
    return key === "source" ? source : category;
  }

  return (
    <div className="filterbar">
      <div className="filter-row">
        <span className="filter-label">Fontes</span>
        <button
          className={`chip${!source ? " active" : ""}`}
          onClick={() => onChange({ source: "" })}
        >
          Todas
        </button>
        {sources.map((s) => (
          <button
            key={s.slug}
            className={`chip${source === s.slug ? " active" : ""}`}
            onClick={() => pick("source", s.slug)}
          >
            {s.name}
          </button>
        ))}
      </div>

      {categories.length > 0 && (
        <div className="filter-row">
          <span className="filter-label">Categorias</span>
          <button
            className={`chip${!category ? " active" : ""}`}
            onClick={() => onChange({ category: "" })}
          >
            Todas
          </button>
          {categories.map((c) => (
            <button
              key={c.slug}
              className={`chip${category === c.slug ? " active" : ""}`}
              onClick={() => pick("category", c.slug)}
            >
              {c.name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
