import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useNavigate, useSearchParams } from "react-router-dom";
import { Bookmark, LogOut, Search } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [q, setQ] = useState(params.get("q") || "");
  const timer = useRef(null);

  // Mantém o campo sincronizado quando a URL muda externamente.
  useEffect(() => {
    setQ(params.get("q") || "");
  }, [params]);

  function onChange(e) {
    const value = e.target.value;
    setQ(value);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      const next = new URLSearchParams(window.location.search);
      value ? next.set("q", value) : next.delete("q");
      navigate(`/?${next.toString()}`);
    }, 350);
  }

  return (
    <header className="navbar">
      <div className="container navbar-inner">
        <Link to="/" className="brand" aria-label="TechCurator — início">
          <span className="brand-mark">T</span>
          <span className="brand-text">
            <span className="brand-name">Tech<b>Curator</b></span>
            <span className="brand-tagline">curadoria de tecnologia</span>
          </span>
        </Link>

        <div className="search">
          <Search size={18} />
          <input
            value={q}
            onChange={onChange}
            placeholder="Buscar por IA, chips, criptomoedas…"
            aria-label="Buscar notícias"
          />
        </div>

        <nav className="nav-actions">
          <NavLink to="/" className="nav-link" end>
            Início
          </NavLink>
          {isAuthenticated && (
            <NavLink to="/salvos" className="nav-link">
              Salvos
            </NavLink>
          )}

          {isAuthenticated ? (
            <>
              <Link to="/salvos" className="btn btn-ghost btn-sm" title="Notícias salvas">
                <Bookmark size={16} /> {user?.username}
              </Link>
              <button className="btn btn-sm" onClick={logout} title="Sair">
                <LogOut size={16} /> Sair
              </button>
            </>
          ) : (
            <>
              <Link to="/entrar" className="btn btn-sm">Entrar</Link>
              <Link to="/registrar" className="btn btn-primary btn-sm">Criar conta</Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
