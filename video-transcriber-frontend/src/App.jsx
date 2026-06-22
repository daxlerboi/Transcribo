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

function ClipboardIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="currentColor">
      <path d="M5 2.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5zm0 3a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5zm-1 2a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7a.5.5 0 0 1-.5-.5zm0 3a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7a.5.5 0 0 1-.5-.5z"/>
    </svg>
  );
}

function SunIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="currentColor">
      <path d="M8 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-1 0v-1A.5.5 0 0 1 8 1zm0 10a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm5.657-6.657a.5.5 0 0 1 0 .707l-.707.707a.5.5 0 1 1-.707-.707l.707-.707a.5.5 0 0 1 .707 0zM13.5 8a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 0 1h-1a.5.5 0 0 1-.5-.5zm-2.157 4.157a.5.5 0 0 1 0 .707l-.707.707a.5.5 0 1 1-.707-.707l.707-.707a.5.5 0 0 1 .707 0zM8 13.5a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-1 0v-1a.5.5 0 0 1 .5-.5zm-4.486-1.343a.5.5 0 0 1 0-.707l.707-.707a.5.5 0 1 1 .707.707l-.707.707a.5.5 0 0 1-.707 0zM1 8a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 0 1h-1A.5.5 0 0 1 1 8zm2.757-6.071a.5.5 0 0 1 0 .707L3.05 3.343a.5.5 0 1 1-.707-.707l.707-.707a.5.5 0 0 1 .707 0z"/>
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="currentColor">
      <path d="M6 .278a.768.768 0 0 1 .08.858 7.208 7.208 0 0 0-.878 3.46c0 4.021 3.278 7.277 7.318 7.277.527 0 1.04-.055 1.533-.16a.787.787 0 0 1 .81.316.733.733 0 0 1-.031.893A8.37 8.37 0 0 1 8 16c-4.418 0-8-3.582-8-8a8.109 8.109 0 0 1 5.795-7.722.768.768 0 0 1 .205 0z"/>
    </svg>
  );
}

function DownloadIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="currentColor">
      <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
      <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="currentColor" style={{width:12,height:12,opacity:0.5}}>
      <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
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
  const [searchQuery, setSearchQuery] = useState("");
  const filtered = searchQuery.trim()
    ? history.filter((h) => h.title?.toLowerCase().includes(searchQuery.toLowerCase()))
    : history;

  return open && (
    <>
      <div className="sidebar-overlay" onClick={onClose} />
      <div className="sidebar">
        <div className="sidebar-header">
          <button className="new-chat-btn" onClick={onNewChat}>
            <PlusIcon /> New transcription
          </button>
        </div>
        {history.length > 0 && (
          <div className="sidebar-search">
            <input
              className="sidebar-search-input"
              placeholder="Search history..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              autoFocus
            />
          </div>
        )}
        <div className="sidebar-list">
          {filtered.length === 0 ? (
            <div className="sidebar-empty">
              {searchQuery ? "No matches found." : "No transcriptions yet.\nPaste a URL and transcribe."}
            </div>
          ) : filtered.map((item) => (
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
  const [dark, setDark] = useState(() => localStorage.getItem("transcribo-theme") === "dark");
  const [exportOpen, setExportOpen] = useState(false);
  const [segmentCopied, setSegmentCopied] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);
  const exportRef = useRef(null);
  const urlRef = useRef(null);

  useEffect(() => {
    document.body.parentElement.setAttribute("data-theme", dark ? "dark" : "light");
    localStorage.setItem("transcribo-theme", dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    const handler = (e) => {
      if (exportRef.current && !exportRef.current.contains(e.target)) setExportOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

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

  const notify = (title, body) => {
    if (window.electronAPI?.isElectron) {
      try { window.electronAPI.notify(title, body); } catch {}
    }
  };

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
      notify("Transcription complete", data.platform === "local" ? "File transcribed successfully" : `URL transcribed: ${data.text?.slice(0, 60)}...`);
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
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      handleTranscribe();
    } else if (e.key === "Enter" && url.trim()) {
      handleTranscribe();
    }
  };

  useEffect(() => {
    const handler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        if (url.trim() && !loading) handleTranscribe();
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [url, loading, token]);

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
      notify("Transcription complete", `File "${file.name}" transcribed successfully`);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) setFile(f);
  };

  const copyTranscript = () => {
    if (!result) return;
    navigator.clipboard.writeText(result.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const copySegment = (text) => {
    navigator.clipboard.writeText(text);
    setSegmentCopied(text);
    setTimeout(() => setSegmentCopied(null), 1500);
  };

  const formatTime = (s) => {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  const formatTimeSrt = (s) => {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    return `${h.toString().padStart(2,"0")}:${m.toString().padStart(2,"0")}:${sec.toFixed(3).padStart(6,"0")}`;
  };

  const download = (content, filename, mime) => {
    const blob = new Blob([content], { type: mime });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
  };

  const exportTxt = () => {
    if (!result) return;
    download(result.text, `transcribo-${result.platform}-${Date.now()}.txt`, "text/plain");
    setExportOpen(false);
  };

  const exportSrt = () => {
    if (!result?.segments?.length) return;
    const srt = result.segments.map((seg, i) =>
      `${i + 1}\n${formatTimeSrt(seg.start)} --> ${formatTimeSrt(seg.end || seg.start + 2)}\n${seg.text}\n`
    ).join("\n");
    download(srt, `transcribo-${result.platform}-${Date.now()}.srt`, "text/plain");
    setExportOpen(false);
  };

  const exportVtt = () => {
    if (!result?.segments?.length) return;
    const vtt = "WEBVTT\n\n" + result.segments.map((seg, i) =>
      `${formatTimeSrt(seg.start)} --> ${formatTimeSrt(seg.end || seg.start + 2)}\n${seg.text}`
    ).join("\n\n");
    download(vtt, `transcribo-${result.platform}-${Date.now()}.vtt`, "text/vtt");
    setExportOpen(false);
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
            <div className="header-actions">
              <button className="theme-toggle" onClick={() => setDark((d) => !d)} title={dark ? "Light mode" : "Dark mode"}>
                {dark ? <SunIcon /> : <MoonIcon />}
              </button>
              <div className="header-user">
                <span className="user-email">{user?.email}</span>
                <button className="logout-btn" onClick={logout}>Log out</button>
              </div>
            </div>
          </div>
          <p className="subtitle">
            Paste a YouTube or Instagram link, or upload a file
          </p>
        </header>

        <div className="input-area">
          <input
            ref={urlRef}
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

        <div
          className="file-area"
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".mp3,.mp4,.m4a,.wav,.webm,.ogg,.mov,.avi,.mkv"
            onChange={handleFileChange}
            className="file-input-hidden"
          />
          <div
            className={"file-dropzone" + (dragOver ? " drag-over" : "")}
            onClick={() => fileInputRef.current?.click()}
          >
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
                Click to select or drag & drop an audio/video file
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
              <div className="result-actions">
                <div className="export-wrapper" ref={exportRef}>
                  <button className="icon-btn" onClick={() => setExportOpen((o) => !o)} title="Export transcript">
                    <DownloadIcon /> Export
                  </button>
                  {exportOpen && (
                    <div className="export-menu">
                      <button onClick={exportTxt}>.txt (Plain text)</button>
                      <button onClick={exportSrt}>.srt (Subtitles)</button>
                      <button onClick={exportVtt}>.vtt (Web subtitles)</button>
                    </div>
                  )}
                </div>
                <button className="icon-btn" onClick={copyTranscript}>
                  {copied ? "Copied!" : "Copy"}
                </button>
              </div>
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
                      <span className="segment-time" title="Click to copy timestamp">{formatTime(seg.start)}</span>
                      <span className="segment-text">{seg.text}</span>
                      <button className="segment-copy" onClick={() => copySegment(seg.text)} title="Copy segment">
                        {segmentCopied === seg.text ? <span style={{fontSize:10}}>OK</span> : <ClipboardIcon />}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <p className="kbd-hint" style={{textAlign:"center",marginTop:24}}>
          Tip: Press <kbd>Enter</kbd> to transcribe, <kbd>Ctrl</kbd>+<kbd>Enter</kbd> from anywhere
        </p>
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
