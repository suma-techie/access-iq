import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import Logo from "../components/Logo";
import SecurityIllustration from "../components/SecurityIllustration";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login, user, isLoading } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!isLoading && user) {
      navigate("/dashboard", { replace: true });
    }
  }, [isLoading, user, navigate]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
      
    } catch {
      setError("Invalid email or password");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-visual">
        <SecurityIllustration />
        <p className="auth-visual-caption">Every permission, grounded in evidence before it's granted.</p>
      </div>
      <div className="auth-form-side">
        <form className="auth-card" onSubmit={handleSubmit}>
          <div className="auth-brand">
            <Logo size={32} />
            <h1>AccessIQ</h1>
          </div>
          <p className="subtitle">Sign in to continue</p>
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
