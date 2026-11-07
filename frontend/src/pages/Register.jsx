import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", email: "", password: "" });
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
      await register(form.username, form.email, form.password);
      navigate("/");
    } catch (err) {
      const data = err?.response?.data;
      const first =
        data && typeof data === "object"
          ? Object.values(data).flat()[0]
          : "Não foi possível criar a conta.";
      setError(String(first));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="container page">
      <div className="auth-wrap">
        <div className="auth-card">
          <h1>Criar conta</h1>
          <p className="sub">Leva menos de um minuto.</p>

          {error && <div className="form-error">{error}</div>}

          <form onSubmit={submit}>
            <div className="field">
              <label htmlFor="username">Usuário</label>
              <input id="username" name="username" value={form.username}
                     onChange={update} autoComplete="username" required />
            </div>
            <div className="field">
              <label htmlFor="email">E-mail (opcional)</label>
              <input id="email" name="email" type="email" value={form.email}
                     onChange={update} autoComplete="email" />
            </div>
            <div className="field">
              <label htmlFor="password">Senha</label>
              <input id="password" name="password" type="password"
                     value={form.password} onChange={update}
                     autoComplete="new-password" required />
            </div>
            <button className="btn btn-primary" disabled={busy}>
              {busy ? "Criando…" : "Criar conta"}
            </button>
          </form>

          <div className="auth-foot">
            Já tem conta? <Link to="/entrar">Entrar</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
