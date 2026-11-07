import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function update(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(form.username, form.password);
      navigate("/");
    } catch {
      setError("Usuário ou senha incorretos.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="container page">
      <div className="auth-wrap">
        <div className="auth-card">
          <h1>Entrar</h1>
          <p className="sub">Acesse para salvar e organizar notícias.</p>

          {error && <div className="form-error">{error}</div>}

          <form onSubmit={submit}>
            <div className="field">
              <label htmlFor="username">Usuário</label>
              <input id="username" name="username" value={form.username}
                     onChange={update} autoComplete="username" required />
            </div>
            <div className="field">
              <label htmlFor="password">Senha</label>
              <input id="password" name="password" type="password"
                     value={form.password} onChange={update}
                     autoComplete="current-password" required />
            </div>
            <button className="btn btn-primary" disabled={busy}>
              {busy ? "Entrando…" : "Entrar"}
            </button>
          </form>

          <div className="auth-foot">
            Ainda não tem conta? <Link to="/registrar">Criar conta</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
