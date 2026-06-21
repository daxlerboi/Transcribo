import { useState, useEffect, useCallback, useRef } from "react";
import { useAuth } from "./AuthContext.jsx";
import "./App.css";

function WaveIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 12v-2a3 3 0 0 1 3-3" opacity="0.4"/>
      <path d="M7 12V8a2 2 0 0 1 4 0v8a2 2 0 0 0 4 0V6a3 3 0 0 1 3 3v3" opacity="0.4"/>
      <path d="M17 12v4a2 2 0 0 0 4 0v-2"/>
      <path d="M11 12V6a2 2 0 0 1 4 0v12a2 2 0 0 0 4 0"/>
    </svg>
  );
}

function YouTubeIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.4.6A3 3 0 0 0 .5 6.2 32 32 0 0 0 0 12a32 32 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.6 9.4.6 9.4.6s7.5 0 9.4-.6a3 3 0 0 0 2.1-2.1 32 32 0 0 0 .5-5.8 32 32 0 0 0-.5-5.8zM9.5 15.5V8.5l6.3 3.5-6.3 3.5z"/>
    </svg>
  );
}

function InstagramIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="2" width="20" height="20" rx="5"/>
      <circle cx="12" cy="12" r="5"/>
      <circle cx="17.5" cy="6.5" r="1.2" fill="currentColor" stroke="none"/>
    </svg>
  );
}

function HamburgerIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="3" y1="6" x2="21" y2="6"/>
      <line x1="3" y1="12" x2="21" y2="12"/>
      <line x1="3" y1="18" x2="21" y2="18"/>
    </svg>
  );
}

function PlusIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="5" x2="12" y2="19"/>
      <line x1="5" y1="12" x2="19" y2="12"/>
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 6h18"/>
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
      <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
    </svg>
  );
}

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
        <WaveIcon className="auth-logo" />
        <h1>Transcribo</h1>
        <h2>{mode === "login" ? "Sign in to your account" : "Create your account"}</h2>
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

function Sidebar({ open, onClose, history, activeId, onSelect, onDelete, onNewChat }) {
  return open && (
    <>
      <div className="sidebar-overlay" onClick={onClose} />
      <div className="sidebar">
        <div className="sidebar-header">
          <button className="new-chat-btn" onClick={onNewChat}>
            <PlusIcon /> New transcription
          </button>
        </div>
        <div className="sidebar-list">
          {history.length === 0 ? (
            <div className="sidebar-empty">
              No transcriptions yet.<br />Paste a URL and transcribe.
            </div>
          ) : history.map((item) => (
            <div
              key={item.id}
              className={"history-item" + (item.id === activeId ? " active" : "")}
              onClick={() => { onSelect(item.id); onClose(); }}
            >
              <div className="history-item-content">
                <div className="history-item-title">{item.title}</div>
                <div className="history-item-meta">
                  {item.platform} · {new Date(item.created_at).toLocaleDateString()}
                </div>
              </div>
              <button
                className="history-item-delete"
                onClick={(e) => { e.stopPropagation(); onDelete(item.id); }}
                title="Delete"
              >
                <TrashIcon />
              </button>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

function TranscribePage() {
  const { user, logout, token } = useAuth();
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [history, setHistory] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [file, setFile] = useState(null);
  const fileInputRef = useRef(null);

  const loadHistory = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch("/api/history", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) setHistory(await res.json());
    } catch {}
  }, [token]);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  const handleTranscribe = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    setCopied(false);
    try {
      const res = await fetch("/api/transcribe", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ url: url.trim() }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || `Server error (${res.status})`);
      }
      const data = await res.json();
      setResult(data);
      setActiveId(null);
      await loadHistory();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const loadFromHistory = async (id) => {
    try {
      const res = await fetch(`/api/history/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const item = await res.json();
        setUrl(item.url);
        setResult(item);
        setActiveId(id);
        setError("");
      }
    } catch (e) {
      setError(e.message);
    }
  };

  const deleteFromHistory = async (id) => {
    try {
      await fetch(`/api/history/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (activeId === id) {
        setResult(null);
        setActiveId(null);
      }
      await loadHistory();
    } catch {}
  };

  const newChat = () => {
    setUrl("");
    setResult(null);
    setError("");
    setActiveId(null);
    setFile(null);
    setSidebarOpen(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleTranscribe();
  };

  const handleFileChange = (e) => {
    const f = e.target.files?.[0];
    if (f) setFile(f);
  };

  const handleFileTranscribe = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    setResult(null);
    setCopied(false);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch("/api/transcribe-file", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || `Server error (${res.status})`);
      }
      const data = await res.json();
      setResult(data);
      setActiveId(null);
      await loadHistory();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
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
    <div className="app-layout">
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        history={history}
        activeId={activeId}
        onSelect={loadFromHistory}
        onDelete={deleteFromHistory}
        onNewChat={newChat}
      />

      <div className="app-main">
        <header className="header">
          <div className="header-top">
            <div className="header-brand">
              <button className="sidebar-toggle" onClick={() => setSidebarOpen(true)} title="History">
                <HamburgerIcon />
              </button>
              <WaveIcon />
              <h1>Transcribo</h1>
            </div>
            <div className="header-user">
              <span className="user-email">{user?.email}</span>
              <button className="logout-btn" onClick={logout}>Log out</button>
            </div>
          </div>
          <p className="subtitle">
            Paste a YouTube or Instagram link, or upload a file
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

        <div className="file-area">
          <input
            ref={fileInputRef}
            type="file"
            accept=".mp3,.mp4,.m4a,.wav,.webm,.ogg,.mov,.avi,.mkv"
            onChange={handleFileChange}
            className="file-input-hidden"
          />
          <div className="file-dropzone" onClick={() => fileInputRef.current?.click()}>
            {file ? (
              <div className="file-selected">
                <span className="file-name">{file.name}</span>
                <span className="file-size">{(file.size / 1024 / 1024).toFixed(1)} MB</span>
                <button className="file-clear" onClick={(e) => { e.stopPropagation(); setFile(null); }}>
                  Remove
                </button>
              </div>
            ) : (
              <span className="file-placeholder">
                Click to select an audio/video file
              </span>
            )}
          </div>
          {file && (
            <button
              className="transcribe-btn"
              onClick={handleFileTranscribe}
              disabled={loading}
            >
              {loading ? <span className="spinner" /> : "Transcribe file"}
            </button>
          )}
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
                {result.platform === "youtube" ? <><YouTubeIcon /> YouTube</> : result.platform === "instagram" ? <><InstagramIcon /> Instagram</> : <><WaveIcon /> Local file</>}
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
