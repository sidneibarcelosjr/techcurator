import { useEffect, useState } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Saved from "./pages/Saved";
import Login from "./pages/Login";
import Register from "./pages/Register";
import { useAuth } from "./context/AuthContext";

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div className="spinner" />;
  return isAuthenticated ? children : <Navigate to="/entrar" replace />;
}

function Toast({ message, onDone }) {
  useEffect(() => {
    const t = setTimeout(onDone, 2600);
    return () => clearTimeout(t);
  }, [onDone]);
  return <div className="toast">{message}</div>;
}

export default function App() {
  const { loading } = useAuth();
  const navigate = useNavigate();
  const [toast, setToast] = useState("");

  function needAuth() {
    setToast("Entre para salvar notícias.");
    setTimeout(() => navigate("/entrar"), 700);
  }

  if (loading) {
    return (
      <div className="app-shell">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div className="app-shell">
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<Home onNeedAuth={needAuth} />} />
          <Route
            path="/salvos"
            element={
              <ProtectedRoute>
                <Saved />
              </ProtectedRoute>
            }
          />
          <Route path="/entrar" element={<Login />} />
          <Route path="/registrar" element={<Register />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <footer className="footer">
        <div className="container">
          <span>TechCurator · Curadoria inteligente de tecnologia</span>
          <span>Web scraping + NLP · 23 portais brasileiros</span>
        </div>
      </footer>
      {toast && <Toast message={toast} onDone={() => setToast("")} />}
    </div>
  );
}
