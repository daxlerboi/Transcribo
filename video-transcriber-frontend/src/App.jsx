import { useState } from "react";
import { useAuth } from "./AuthContext.jsx";
import "./App.css";

function AuthPage({ mode, onSwitch, onSuccess }) {
  const { login, register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const fn = mode === "login" ? login : register;
      await fn(email, password);
      onSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Transcribo</h1>
        <h2>{mode === "login" ? "Sign in" : "Create account"}</h2>
        <form onSubmit={handleSubmit}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={busy}
          />
          <input
            type="password"
            placeholder="Password (min 6 chars)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
            disabled={busy}
          />
          <button type="submit" disabled={busy} className="auth-btn">
            {busy ? <span className="spinner" /> : mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>
        {error && <p className="auth-error">{error}</p>}
        <p className="auth-switch">
          {mode === "login" ? (
            <>No account? <button onClick={() => onSwitch("register")}>Register</button></>
          ) : (
            <>Already have one? <button onClick={() => onSwitch("login")}>Sign in</button></>
          )}
        </p>
      </div>
    </div>
  );
}

function TranscribePage() {
  const { user, logout } = useAuth();
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const handleTranscribe = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    setCopied(false);
    try {
      const res = await fetch("/api/transcribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim() }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || `Server error (${res.status})`);
      }
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleTranscribe();
  };

  const copyTranscript = () => {
    if (!result) return;
    navigator.clipboard.writeText(result.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatTime = (s) => {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-top">
          <h1>Transcribo</h1>
          <div className="header-user">
            <span className="user-email">{user?.email}</span>
            <button className="logout-btn" onClick={logout}>Log out</button>
          </div>
        </div>
        <p className="subtitle">
          Paste a YouTube or Instagram link — get the transcript
        </p>
      </header>

      <div className="input-area">
        <input
          type="url"
          className="url-input"
          placeholder="https://youtube.com/watch?v=... or https://instagram.com/reel/..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button
          className="transcribe-btn"
          onClick={handleTranscribe}
          disabled={loading || !url.trim()}
        >
          {loading ? <span className="spinner" /> : "Transcribe"}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {loading && (
        <div className="loading-bar">
          <div className="loading-fill" />
        </div>
      )}

      {result && (
        <div className="result">
          <div className="result-header">
            <span className={"platform-badge " + result.platform}>
              {result.platform === "youtube" ? "YouTube" : "Instagram"}
            </span>
            <button className="copy-btn" onClick={copyTranscript}>
              {copied ? "Copied!" : "Copy transcript"}
            </button>
          </div>

          <div className="transcript-full">
            <h3>Full transcript</h3>
            <p>{result.text}</p>
          </div>

          {result.segments?.length > 0 && (
            <div className="segments">
              <h3>Segments ({result.segments.length})</h3>
              <div className="segment-list">
                {result.segments.map((seg, i) => (
                  <div className="segment" key={i}>
                    <span className="segment-time">{formatTime(seg.start)}</span>
                    <span className="segment-text">{seg.text}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function App() {
  const { user, loading } = useAuth();
  const [authMode, setAuthMode] = useState("login");

  if (loading) return <div className="loading-screen"><span className="spinner" /></div>;
  if (!user) return <AuthPage mode={authMode} onSwitch={setAuthMode} onSuccess={() => {}} />;
  return <TranscribePage />;
}
