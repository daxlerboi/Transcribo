# Transcribo

[![React](https://img.shields.io/badge/React-20232A?logo=react&logoColor=61DAFB)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white)](https://vite.dev/)
[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Whisper](https://img.shields.io/badge/Whisper-OpenAI-412991)](https://github.com/openai/whisper)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-powered-FF0000?logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)
[![Windows](https://img.shields.io/badge/Windows-supported-0078D4?logo=windows&logoColor=white)](https://www.microsoft.com/windows)

Full-stack video transcription app. Paste a YouTube/Instagram link or upload a local audio/video file — get the full transcript with timestamped segments.

---

## Features

- **YouTube transcripts** — Fetches existing captions via YouTube's API
- **Instagram + other platforms** — Falls back to yt-dlp + Whisper for any video URL
- **Local file upload** — Upload MP3, MP4, WAV, etc. and transcribe with Whisper
- **Multi-language** — Auto-detects available caption languages, picks the best match
- **Timestamped segments** — Full transcript + individual segments with start/end times
- **History sidebar** — ChatGPT-style panel with past transcriptions, searchable, deletable
- **User authentication** — Register, login, logout with JWT (stdlib hashlib + hmac)
- **JSON file storage** — No database server needed, zero config

## Setup

### Prerequisites
- Python 3.13+
- Node.js 24+
- npm 11+

### Install

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../video-transcriber-frontend
npm install
```

### Run

```bash
# Production mode (builds frontend, serves everything on :8000)
start.bat

# Or development (two terminals, hot reload)
cd backend && uvicorn main:app --host 127.0.0.1 --port 8000 --reload
cd video-transcriber-frontend && npm run dev
```

Open **http://localhost:5173** (dev) or **http://localhost:8000** (production).

## Tech Stack

### Frontend
- React 19 + Vite 8
- Plain CSS (zero dependencies)
- JWT stored in localStorage

### Backend
- Python 3.13+ (stdlib only for auth — no passlib, no jose, no bcrypt)
- FastAPI (async)
- youtube-transcript-api (fetch captions)
- yt-dlp (download audio from YouTube/Instagram)
- OpenAI Whisper (speech-to-text, local)
- Uvicorn (ASGI server)

### Database
- **JSON file** only (`backend/data.json`) — no MongoDB, no SQLite, no server needed
- All stdlib hashing: `hashlib.pbkdf2_hmac` + `hmac` + `base64` for JWT

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/register` | No | Create account |
| POST | `/api/auth/login` | No | Sign in |
| POST | `/api/auth/logout` | Yes | Revoke token |
| GET | `/api/auth/me` | Yes | Current user |
| POST | `/api/transcribe` | Yes | Transcribe YouTube/Instagram URL |
| POST | `/api/transcribe-file` | Yes | Transcribe uploaded file |
| GET | `/api/history` | Yes | List transcriptions |
| GET | `/api/history/{id}` | Yes | Get transcription detail |
| PATCH | `/api/history/{id}/title` | Yes | Rename transcription |
| DELETE | `/api/history/{id}` | Yes | Delete transcription |
| GET | `/api/health` | No | Health check |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET` | `dev-secret` | Secret for signing JWT tokens |
| `YOUTUBE_COOKIES` | — | Base64-encoded JSON cookies (bypass YouTube IP block) |
| `WHISPER_ENABLED` | `1` | Set to `0` to disable Whisper on low-memory servers |

## Project Structure

```
video-transcriber/
├── backend/
│   ├── main.py              # FastAPI server — routes, CORS, static frontend
│   ├── auth.py              # Auth routes (stdlib JWT + hashing)
│   ├── transcriber.py       # YouTube API + Whisper + file transcription
│   ├── database.py          # JSON file storage
│   ├── data.json            # Database file (gitignored, auto-created)
│   ├── data.sample.json     # Template for data.json
│   ├── requirements.txt     # Python deps (pure Python only)
│   └── serve.bat            # Background server launcher
├── video-transcriber-frontend/
│   ├── src/
│   │   ├── main.jsx         # React entry point
│   │   ├── App.jsx          # Main app: auth, transcribe, file upload, sidebar
│   │   ├── AuthContext.jsx  # Auth state (JWT in localStorage)
│   │   ├── App.css          # Styles
│   │   └── index.css        # Global styles
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── start.bat                # One-click launcher (build + serve)
└── README.md
```

## Notes

- **Render deploy** — YouTube blocks Render's IP range. Set `YOUTUBE_COOKIES` env var with browser cookies to bypass, or run locally.
- **Whisper on Render** — Disabled by default (512MB RAM can't load 1.5GB model). Set `WHISPER_ENABLED=0`.
- **History** — Auto-saves every transcription. Sidebar shows all past transcriptions with rename/delete.
- **All stdlib auth** — No passlib, no bcrypt, no python-jose. Uses `hashlib` + `hmac` for everything.

---

Built by `daxler_boi`
