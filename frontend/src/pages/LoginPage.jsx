import { useState } from "react";
import {
  Eye,
  EyeOff,
  FileSearch,
  Languages,
  Lock,
  Mail,
  ShieldAlert,
  ShieldCheck,
  User,
} from "lucide-react";
import apiClient from "../api/client";

function LoginPage({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      if (mode === "register") {
        await apiClient.post("/auth/register", {
          full_name: fullName,
          email,
          password,
        });

        setSuccess("Account created successfully. Please login now.");
        setMode("login");
        setPassword("");
        return;
      }

      const response = await apiClient.post("/auth/login", {
        email,
        password,
      });

      localStorage.setItem("access_token", response.data.access_token);
      localStorage.setItem("user", JSON.stringify(response.data.user));

      onLogin(response.data.user);
    } catch (err) {
      const backendMessage =
        err.response?.data?.detail || "Something went wrong. Please try again.";

      if (mode === "register") {
        setError(
          typeof backendMessage === "string"
            ? backendMessage
            : "Registration failed. Please check your details."
        );
      } else {
        setError("Login failed. Please check your email and password.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-visual">
        <div className="login-brand">
          <div className="brand-logo">
            <ShieldCheck size={22} />
          </div>
          <strong>Red Alert AI</strong>
        </div>

        <div className="login-hero">
          <p className="eyebrow">Document risk scanner</p>
          <h1>Know what is inside a document before you share it.</h1>
          <p className="hero-copy">
            Upload a PDF, Word file, text file or scanned image. Red Alert AI
            finds threats, fraud signals, policy violations and personal data,
            and explains every point of its risk score.
          </p>

          <ul className="feature-list">
            <li>
              <ShieldAlert size={18} />
              Threat, fraud and policy-violation detection
            </li>
            <li>
              <FileSearch size={18} />
              Aadhaar, PAN, card and bank detail detection
            </li>
            <li>
              <Languages size={18} />
              English and Gujarati documents
            </li>
          </ul>
        </div>

        <div className="risk-strip">
          <span><span className="dot green" /> Green · 0–30</span>
          <span><span className="dot yellow" /> Yellow · 31–70</span>
          <span><span className="dot red" /> Red · 71–100</span>
        </div>
      </section>

      <section className="login-panel">
        <div className="panel-header">
          <div>
            <h2>{mode === "login" ? "Welcome back" : "Create your account"}</h2>
            <p>
              {mode === "login"
                ? "Log in to scan and review your documents."
                : "It only takes a moment to get started."}
            </p>
          </div>
        </div>

        <div className="auth-switch">
          <button
            type="button"
            className={mode === "login" ? "active" : ""}
            onClick={() => {
              setMode("login");
              setError("");
              setSuccess("");
            }}
          >
            Log in
          </button>

          <button
            type="button"
            className={mode === "register" ? "active" : ""}
            onClick={() => {
              setMode("register");
              setError("");
              setSuccess("");
            }}
          >
            Register
          </button>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {mode === "register" && (
            <label>
              Full Name
              <div className="input-box">
                <User size={18} />
                <input
                  type="text"
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  placeholder="Enter full name"
                  required
                />
              </div>
            </label>
          )}

          <label>
            Email Address
            <div className="input-box">
              <Mail size={18} />
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
                required
              />
            </div>
          </label>

          <label>
            Password
            <div className="input-box">
              <Lock size={18} />
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder={mode === "login" ? "Your password" : "Choose a password"}
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                required
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword((visible) => !visible)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </label>

          {error && <p className="form-error">{error}</p>}
          {success && <p className="form-success">{success}</p>}

          <button type="submit" className="button primary large" disabled={loading}>
            {loading
              ? mode === "login"
                ? "Logging in…"
                : "Creating account…"
              : mode === "login"
                ? "Log in"
                : "Create account"}
          </button>
        </form>
      </section>
    </main>
  );
}

export default LoginPage;