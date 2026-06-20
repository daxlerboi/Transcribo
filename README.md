# Transcribo

[![React](https://img.shields.io/badge/React-20232A?logo=react&logoColor=61DAFB)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white)](https://vite.dev/)
[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-ready-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Whisper](https://img.shields.io/badge/Whisper-OpenAI-412991)](https://github.com/openai/whisper)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-powered-FF0000?logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)
[![JWT](https://img.shields.io/badge/JWT-auth-000000?logo=jsonwebtokens&logoColor=white)](https://jwt.io/)
[![Windows](https://img.shields.io/badge/Windows-supported-0078D4?logo=windows&logoColor=white)](https://www.microsoft.com/windows)

Built by `daxler_boi`

Transcribo is a full-stack video transcription web app. Paste a YouTube or Instagram link — get the full transcript with timestamped segments instantly.

---

## What It Does

- **YouTube transcripts** — Fetches existing captions instantly via YouTube's API. No download. No GPU.
- **Instagram + other platforms** — Falls back to yt-dlp + OpenAI Whisper for any video URL.
- **Multi-language** — Auto-detects available caption languages across 12 languages, picks the best match.
- **Timestamped segments** — Returns the full transcript plus individual segments with start/end times.
- **Copy to clipboard** — One-click copy of the full transcript text.
- **User authentication** — Register, login, logout with JWT-based sessions. Server-side token blacklist on logout.
- **Security-first** — CORS locked to specific origins, SSRF guard, URL validation, bcrypt hashing, temp file cleanup.

---

## How It Is Built

The project follows a two-tier architecture:

1. **React frontend** (Vite dev server) communicates with a **FastAPI backend** via REST. Vite proxies `/api/*` requests to avoid CORS issues in development.
2. The backend runs two independent systems:
   - **Auth system** — JWT-based register/login/logout with bcrypt password hashing and server-side token blacklist.
   - **Transcription pipeline** — Two tiers: YouTube Transcript API (instant) and yt-dlp + Whisper (download + transcribe fallback).

The frontend handles three states: loading (token validation), auth page (login/register), and transcribe page (the main interface). The backend handles URL validation, platform detection, language selection, and transcription orchestration.

The database layer uses a JSON file in development (no server needed) and swaps to MongoDB in production via a single `.env` variable — no code changes required.

---

## Tech Stack

### Frontend

- **React 19** — UI framework
- **Vite 8** — Build tool and dev server
- **CSS** — Plain CSS (no framework, no dependencies)

### Backend

- **Python 3.13+** — Runtime
- **FastAPI** — REST API framework (async)
- **Jose (python-jose)** — JWT token creation and verification
- **Passlib + bcrypt** — Password hashing
- **youtube-transcript-api** — Fetch existing YouTube captions (instant)
- **yt-dlp** — Download audio from YouTube/Instagram
- **OpenAI Whisper** — Speech-to-text (fallback for non-caption videos)
- **Uvicorn** — ASGI server

### Database

- **JSON file** (development) — No database server needed
- **MongoDB** (production) — Swappable via a single `.env` variable

---

## Architecture Overview

```
User's Browser
      │
      ▼
React App (localhost:5173)
      │
      │  /api/* proxied by Vite
      ▼
FastAPI Backend (localhost:8000)
      │
      ├──► Auth System ──► Database (JSON/MongoDB)
      │      ├─ POST /api/auth/register
      │      ├─ POST /api/auth/login
      │      ├─ POST /api/auth/logout
      │      └─ GET  /api/auth/me
      │
      └──► Transcription Pipeline
             ├─ YouTube URL ──► YouTube Transcript API (instant)
             └─ Other URL   ──► yt-dlp + Whisper (download + transcribe)
```

The frontend and backend communicate via REST. The Vite dev server proxies `/api/*` requests to the FastAPI backend to avoid CORS issues in development. In production, both are served from the same domain or CORS is configured explicitly.

---

## Code Walkthrough

### Backend

#### `backend/main.py`
The FastAPI application entry point.

- Creates the FastAPI app with CORS middleware (pinned to `localhost:5173` and `localhost:4173`)
- Includes the auth router (`/api/auth/*`)
- Defines the `/api/transcribe` endpoint — accepts a `{ "url": "..." }` body, validates the URL, then runs the transcription pipeline asynchronously with a 10-minute timeout
- `/api/health` — simple health check endpoint

Key implementation details:
```python
# URL validation happens before any processing
validate_url(req.url)

# Heavy transcription runs in a thread pool to not block the event loop
result = await asyncio.wait_for(
    asyncio.get_event_loop().run_in_executor(None, process_url, req.url),
    timeout=600,
)
```

#### `backend/auth.py`
Authentication system with JWT.

- **Register** (`POST /api/auth/register`) — Validates email + password (min 6 chars), checks for duplicates, hashes password with bcrypt, stores user, returns JWT token
- **Login** (`POST /api/auth/login`) — Finds user by email, verifies password hash, returns JWT token
- **Logout** (`POST /api/auth/logout`) — Adds the current token to a blacklist stored on the user document
- **Me** (`GET /api/auth/me`) — Returns the authenticated user's info
- **JWT creation** — Tokens contain `sub` (email) and `exp` (7 days from now), signed with HS256
- **Auth middleware** — `get_current_user()` dependency decodes the JWT, looks up the user, checks the token blacklist

```python
SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = timedelta(days=7)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

#### `backend/transcriber.py`
The core transcription engine.

- **`validate_url(url)`** — Security filter:
  - Checks URL is not empty and under 2048 chars
  - Only allows `http` and `https` schemes (blocks `file://`, `ftp://`, etc.)
  - Rejects private/internal IP addresses (127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, ::1)
- **`extract_video_id(url)`** — Extracts the 11-character YouTube video ID from various URL formats (`/watch?v=`, `youtu.be/`, `/shorts/`)
- **`detect_platform(url)`** — Identifies YouTube vs Instagram vs unknown
- **`get_youtube_transcript(video_id)`** — Queries the YouTube Transcript API, tries multiple languages in preference order
- **`download_audio(url)`** — Uses yt-dlp to download the worst-quality audio stream (fastest), converts to MP3. Creates a temp directory for each download, cleans up on both success and failure.
- **`transcribe_audio(audio_path)`** — Loads Whisper's `base` model, transcribes the audio file, returns text + segments
- **`process_url(url)`** — Orchestrator: tries YouTube API first, falls back to download + Whisper

#### `backend/database.py`
Database abstraction layer.

- Implements a MongoDB-compatible interface using a local JSON file
- Methods: `find_one()`, `insert_one()`, `update_one()`, `delete_one()`
- Each method takes `collection` (string) and `query` (dict) parameters — same as MongoDB
- Auto-assigns UUIDs to new documents
- Auto-saves to disk after every write operation
- Thread-safe for single-process use
- When `MONGODB_URL` is set in `.env`, swap this file for `motor` (async MongoDB driver) without changing any other code

```python
db.find_one("users", {"email": "user@example.com"})
db.insert_one("users", {"email": "...", "password": "..."})
db.update_one("users", {"email": "..."}, {"tokens_blacklisted": [...]})
```

#### `backend/requirements.txt`
```
fastapi>=0.115
uvicorn>=0.32
openai-whisper>=20240930
yt-dlp>=2024.12
pydantic>=2.0
python-multipart>=0.0.18
python-jose[cryptography]>=3.3
passlib[bcrypt]>=1.7
python-dotenv>=1.0
motor>=3.0
```

#### `backend/start_server.vbs`
Windows VBScript that launches the backend in a hidden window. Used by `start.bat` and for manual startup without a visible command prompt.

```vbscript
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d D:\...\backend && uvicorn main:app --host 127.0.0.1 --port 8000 --timeout-keep-alive 600", 0, False
```

#### `backend/data.sample.json`
Template for the database file. Copy to `data.json` on first setup:
```json
{"users": []}
```

---

### Frontend

#### `video-transcriber-frontend/src/main.jsx`
React entry point. Wraps the entire app in `AuthProvider` (from `AuthContext.jsx`) to make auth state available everywhere.

```jsx
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </StrictMode>,
)
```

#### `video-transcriber-frontend/src/App.jsx`
Main application component. Contains three logical views:

1. **Loading screen** — Shown while checking if an existing JWT token is still valid
2. **Auth page** — Login or Register form (toggled by the user). Handles form submission, error display, and mode switching.
3. **Transcribe page** — The main interface:
   - Header with app name + user email + Log out button
   - Text input for pasting video URL
   - Transcribe button with loading spinner
   - Error display area
   - Results section: platform badge, full transcript, timestamped segment list, copy button

Authentication flow:
```jsx
export default function App() {
  const { user, loading } = useAuth();
  if (loading) return <LoadingScreen />;
  if (!user) return <AuthPage />;
  return <TranscribePage />;
}
```

#### `video-transcriber-frontend/src/AuthContext.jsx`
React context for authentication state management.

- **State**: `user`, `token`, `loading`
- **On mount**: Checks if a token exists in localStorage, validates it against `/api/auth/me`, clears invalid tokens
- **`login(email, password)`**: Sends POST to `/api/auth/login`, stores token, sets user
- **`register(email, password)`**: Sends POST to `/api/auth/register`, stores token, sets user
- **`logout()`**: Sends POST to `/api/auth/logout`, clears token and user state
- Robust JSON parsing with fallback error handling

```jsx
const AuthContext = createContext(null);
export function useAuth() { ... }  // Hook for consuming components
```

#### `video-transcriber-frontend/src/App.css`
Complete styling for the application. Covers:

- App container layout (max-width 720px, centered)
- Header with title, subtitle, user email, and logout button
- URL input field and Transcribe button
- Loading spinner animation
- Progress bar animation
- Error message styling
- Result card with platform badge
- Full transcript and segments list
- Auth page (centered card layout)
- Auth form inputs and submit button
- Auth switch (Login/Register toggle)
- Loading screen

#### `video-transcriber-frontend/src/index.css`
Global base styles: box-sizing reset, body background, font, root layout.

#### `video-transcriber-frontend/vite.config.js`
Vite configuration with API proxy for development. Proxies `/api/*` requests to the FastAPI backend on port 8000, with a 10-minute timeout for long transcriptions.

```js
server: {
  proxy: {
    "/api": {
      target: "http://127.0.0.1:8000",
      changeOrigin: true,
      timeout: 600000,
      proxyTimeout: 600000,
    },
  },
},
```

#### `video-transcriber-frontend/index.html`
HTML entry point with the app title "Transcribo — Video Transcriber".

#### `video-transcriber-frontend/package.json`
Node dependencies: `react`, `react-dom` (runtime), `vite`, `@vitejs/plugin-react`, `eslint` (dev).

---

### Database

**Current (development):** `backend/data.json`

A simple JSON file that implements MongoDB-compatible CRUD operations. All user records and blacklisted tokens are stored here. The file is gitignored — each developer or deployment gets their own copy.

**Database interface (`backend/database.py`):**
```python
# All methods follow MongoDB conventions
find_one(collection, query)           # Returns first matching doc or None
insert_one(collection, doc)           # Returns doc with auto-assigned _id
update_one(collection, query, update) # Returns True/False
delete_one(collection, query)         # Returns True/False
```

**Document schema (`users` collection):**
```json
{
  "_id": "uuid-string",
  "email": "user@example.com",
  "password": "$2b$12$hashed_bcrypt...",
  "tokens_blacklisted": ["eyJ...", "eyJ..."],
  "created_at": "2026-06-19T17:30:00+00:00"
}
```

**To switch to MongoDB:** Set `MONGODB_URL` in `backend/.env`. The `database.py` module detects this and swaps from JSON file to `motor` (async MongoDB driver). No code changes needed.

---

### Root

#### `start.bat`
Windows batch script that launches both servers in separate windows:
```
start "Transcribo Backend" cmd /c "cd ...backend && uvicorn main:app ..."
start "Transcribo Frontend" cmd /c "cd ...frontend && npm run dev"
```

#### `.gitignore`
Ignores: Python cache files, virtual environments, `node_modules`, build output, `.env` files with secrets, the local database file (`data.json`), OS files, IDE config.

#### `opendesign/`
OpenDesign design system viewer. Contains:
- `index.html` — Design artifact viewer
- `manifest.json` — Design system manifest

---

## Setup & Running

### Prerequisites
- Python 3.13+
- Node.js 24+
- npm 11+

### 1. Clone and install dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../video-transcriber-frontend
npm install
```

### 2. Copy the database template

```bash
copy backend\data.sample.json backend\data.json
```

Or on Linux/macOS:
```bash
cp backend/data.sample.json backend/data.json
```

### 3. Start both servers

**Option A — Double-click `start.bat` (Windows only)**

**Option B — Two terminals:**

Terminal 1 (Backend):
```bash
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000 --timeout-keep-alive 600
```

Terminal 2 (Frontend):
```bash
cd video-transcriber-frontend
npm run dev
```

### 4. Open the app

http://localhost:5173

---

## Authentication Flow

```
Register / Login
      │
      ▼
User submits email + password
      │
      ▼
Backend validates input
      │
      ├── Register: checks for duplicates, hashes password, stores user
      └── Login: finds user, verifies password hash
      │
      ▼
Backend creates JWT token (HS256, 7-day expiry)
      │
      ▼
Frontend stores token in localStorage
      │
      ▼
User is logged in — sees the Transcribe page
      │
      ▼
On every page load, token is validated via GET /api/auth/me
If invalid/expired → user is logged out automatically

Logout
      │
      ▼
Token is added to server-side blacklist
Token removed from localStorage
User sees the login page again
```

---

## Transcription Pipeline

```
User pastes URL and clicks Transcribe
      │
      ▼
URL validation (main.py → validate_url in transcriber.py)
  ├── Checks http/https scheme only
  ├── Blocks private IP addresses
  └── Limits URL length to 2048 chars
      │
      ▼
Platform detection (transcriber.py → detect_platform)
      │
      ├── YouTube ──► extract_video_id()
      │                   │
      │                   ▼
      │             YouTube Transcript API
      │                   │
      │             Available languages? ──► Pick best match
      │                   │                       │
      │               Found ──► Return transcript  │
      │                   │                       │
      │               Not found ───────────────────┘
      │                   │
      │                   ▼
      │             Fall through to download
      │
      └── Other (Instagram, etc.)
              │
              ▼
      yt-dlp downloads audio (worst quality, MP3)
              │
              ▼
      OpenAI Whisper transcribes (base model)
              │
              ▼
      Returns text + timestamped segments
              │
              ▼
      Temp files cleaned up (success or error)
```

---

## Database Layer

### Local Development (JSON File)

**File:** `backend/data.json` (gitignored)

No database server to install. No daemon to run. The file is created automatically on first write.

```json
{"users": []}
```

All CRUD operations are atomic (write to disk on every change). Safe for single-process development.

**Performance:** Good for up to ~10,000 users locally. Beyond that, switch to MongoDB.

### Switching to MongoDB

1. Create `backend/.env`:
```
MONGODB_URL=mongodb+srv://username:password@your-cluster.mongodb.net/transcribo
JWT_SECRET=your-64-char-random-secret
```

2. The `database.py` module auto-detects the `MONGODB_URL` env variable and uses `motor` (async MongoDB driver) instead of the JSON file.

3. No code changes needed. The `find_one`, `insert_one`, `update_one`, `delete_one` interface is identical.

**MongoDB Atlas** gives a free 512MB cluster — perfect for production deployment.

---

## API Reference

### Auth Endpoints

#### `POST /api/auth/register`
Create a new account and get a JWT token.

**Request:**
```json
{ "email": "user@example.com", "password": "mypassword" }
```

**Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": { "id": "uuid", "email": "user@example.com" }
}
```

**Errors:** `400` (validation), `409` (duplicate email)

#### `POST /api/auth/login`
Sign in with existing credentials.

**Request:**
```json
{ "email": "user@example.com", "password": "mypassword" }
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": { "id": "uuid", "email": "user@example.com" }
}
```

**Errors:** `401` (invalid credentials)

#### `POST /api/auth/logout`
Revoke the current JWT token.
- **Auth:** Required (Bearer token)
- **Response (200):** `{ "message": "Logged out" }`

#### `GET /api/auth/me`
Get the currently authenticated user.
- **Auth:** Required (Bearer token)
- **Response (200):** `{ "id": "uuid", "email": "user@example.com" }`

### Transcription Endpoint

#### `POST /api/transcribe`
Transcribe a video URL.

**Request:**
```json
{ "url": "https://youtu.be/dQw4w9WgXcQ" }
```

**Response (200):**
```json
{
  "text": "We're no strangers to love...",
  "platform": "youtube",
  "url": "https://youtu.be/dQw4w9WgXcQ",
  "segments": [
    { "start": 1.36, "end": 3.04, "text": "[♪♪♪]" },
    { "start": 3.04, "end": 6.12, "text": "We're no strangers to love..." }
  ]
}
```

**Errors:** `400` (invalid URL), `408` (timeout), `500` (server error)

### Health Check

#### `GET /api/health`
- **Response (200):** `{ "status": "ok" }`

---

## Backend Systems

### 1. FastAPI Web Server (`main.py`)
The core HTTP server. Handles all incoming requests, routing, CORS, and error handling.

- **ASGI server:** Uvicorn on port 8000
- **CORS:** Pinned to specific origins only (`localhost:5173`, `localhost:4173`, `127.0.0.1:5173`) — not wide-open
- **Endpoints:**
  - `POST /api/transcribe` — Transcribe a video URL
  - `GET /api/health` — Health check
- **Async execution:** Heavy transcription runs in a thread pool via `run_in_executor()` so the server stays responsive
- **Timeout:** 10-minute hard limit on transcription requests
- **Body size:** URL capped at 2048 characters via validation

### 2. Authentication System (`auth.py`)
JWT-based auth with register, login, logout, and session verification.

- **Password hashing:** bcrypt (12 rounds) via Passlib — passwords never stored in plaintext
- **JWT tokens:** HS256 signing, 7-day expiry, configurable `JWT_SECRET`
- **Token blacklist:** Logout adds the token to a server-side blacklist (stored per user), making logout irreversible even if the token hasn't expired
- **Password policy:** Minimum 6 characters enforced server-side
- **Deduplication:** Duplicate email registration returns 409 Conflict

### 3. Transcription Engine (`transcriber.py`)
Two-tier transcription pipeline with automatic fallback.

- **Tier 1 — YouTube Transcript API:** Fetches existing captions instantly (no download, no ML). Supports 12 languages with automatic preference ordering.
- **Tier 2 — yt-dlp + Whisper:** Downloads audio (worst quality for speed) and transcribes with OpenAI Whisper `base` model. Used for Instagram or videos without captions.
- **URL validation:** Rejects non-http/https schemes, blocks private/internal IPs (SSRF guard)
- **Multi-language:** Auto-detects available caption languages and picks the best match
- **Temp cleanup:** Isolated temp directories per download, cleaned up on both success and failure

### 4. Database Layer (`database.py`)
MongoDB-compatible CRUD interface backed by a local JSON file.

- **Methods:** `find_one()`, `insert_one()`, `update_one()`, `delete_one()` — same API as MongoDB
- **Auto-save:** Writes to disk after every mutation
- **Auto-ID:** Assigns UUIDs to new documents
- **MongoDB swap:** Set `MONGODB_URL` in `.env` and the same code works with real MongoDB via `motor`
- **Collections:** `users` — stores email, hashed password, token blacklist, timestamps

### 5. YouTube Integration (`youtube-transcript-api`)
Third-party library for fetching YouTube captions.

- Lists available caption languages for any video
- Fetches transcript with timestamps
- Supports auto-generated and manually created captions
- Returns text + duration for each segment

### 6. Audio Downloader (`yt-dlp`)
Command-line tool for downloading audio from video platforms.

- **Flags:** `--no-playlist`, `--no-warnings`, `-f worstaudio`, `--audio-format mp3`, `--audio-quality 5`
- **Timeout:** 10-minute subprocess timeout
- **Error handling:** Captures stderr, raises descriptive error on failure
- **Temp isolation:** Each download in its own temp directory

### 7. Speech-to-Text (`OpenAI Whisper`)
Local ML model for transcribing audio without captions.

- **Model:** `base` (~1.5GB VRAM or runs on CPU)
- **Output:** Full text + timestamped segments with start/end times
- **Auto-downloads** model on first run (cached in `~/.cache/whisper/`)

---

## Security Implementation

All security fixes applied to the backend:

| # | Fix | What changed | File:Line |
|---|-----|-------------|-----------|
| 1 | **CORS locked down** | `allow_origins` pinned to `localhost:5173`, `localhost:4173`, `127.0.0.1:5173` — replaced wide-open `["*"]` | `main.py:14` |
| 2 | **URL scheme validation** | Only `http`/`https` allowed. Blocks `file://`, `ftp://`, `data://`, `javascript://` | `transcriber.py:24-31` |
| 3 | **URL length limit** | Capped at 2048 characters to prevent abuse | `transcriber.py:22` |
| 4 | **SSRF guard** | Blocks private IP ranges: `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1/128` | `transcriber.py:13-19, 33-41` |
| 5 | **Temp dir cleanup** | `download_audio()` now cleans up temp directories on both success AND error (was leaking on exceptions) | `transcriber.py:94-97, 112-116` |
| 6 | **yt-dlp flags** | Added `--no-warnings` to suppress unnecessary output, already had `--no-playlist` | `transcriber.py:101-102` |

### CORS
```python
ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
]
```
Only these origins can make browser requests. All others are rejected with CORS errors.

### URL Validation
- Only `http` and `https` schemes allowed (blocks `file://`, `ftp://`, `data://`, `javascript://`)
- URL length capped at 2048 characters
- Rejects URLs with no hostname
- Raises HTTP 400 with descriptive message on invalid input

### SSRF (Server-Side Request Forgery) Guard
```python
PRIVATE_NETS = [
    ip_network("127.0.0.0/8"),
    ip_network("10.0.0.0/8"),
    ip_network("172.16.0.0/12"),
    ip_network("192.168.0.0/16"),
    ip_network("169.254.0.0/16"),
    ip_network("::1/128"),
]
```
Any URL pointing to a private/internal IP is rejected with HTTP 400. Prevents the server from being used as a proxy to scan internal networks.

### Password Security
- Hashed with **bcrypt** (12 rounds) via Passlib
- Never stored in plaintext
- Minimum 6 characters enforced
- Duplicate email detection (409 Conflict)

### JWT Tokens
- Signed with **HS256** using configurable `JWT_SECRET`
- 7-day expiry
- Server-side **token blacklist** on logout — revoked tokens stored per user, checked on every authenticated request
- Invalid/expired/revoked tokens return 401

### Input Handling
- Request body validated by **Pydantic models** (type checking, required fields)
- URL sanitized before passing to subprocess
- yt-dlp runs with `--no-warnings` and `--no-playlist` flags
- All exceptions return JSON error responses (not HTML or stack traces)

### Temp File Security
- Each download gets an isolated temp directory (UUID-based)
- Directories cleaned up on both success and failure via `_cleanup_dir()`
- Files deleted after transcription completes
- No persistent audio files stored on the server

---

## Deployment

### Option 1: Render (Free Tier)
- **Frontend:** Build with `npm run build`, deploy the `dist/` folder as a static site
- **Backend:** Deploy as a web service with `uvicorn main:app`
- **Database:** Use Render's free PostgreSQL, or MongoDB Atlas free tier
- **Limitation:** Free tier spins down after inactivity (cold start)

### Option 2: VPS ($6/mo Hetzner / DigitalOcean)
- **All-in-one:** Run both servers on the same machine
- **Frontend:** Build and serve via nginx
- **Backend:** Run behind nginx reverse proxy with HTTPS
- **Database:** Full Whisper fallback works (enough RAM)

### Option 3: Railway
- **Frontend + Backend** as two services
- **Database:** MongoDB Atlas or Railway's PostgreSQL plugin
- **Good middle ground** — easier than VPS, more capable than Render free

### Environment Variables (Production)
```
MONGODB_URL=mongodb+srv://...
JWT_SECRET=your-64-char-random-secret
ORIGINS=https://your-frontend.com
```

### HTTPS
Add a reverse proxy (nginx / Caddy / Cloudflare Tunnel) in front of the backend for TLS termination.

---

## Project Structure (Full Tree)

```
video-transcriber/
│
├── backend/
│   ├── main.py                # FastAPI server — CORS, routes, transcribe endpoint
│   ├── auth.py                # Register, Login, Logout, /me — JWT auth
│   ├── transcriber.py         # YouTube Transcript API + Whisper fallback, URL validation
│   ├── database.py            # JSON file database (MongoDB-compatible interface)
│   ├── data.sample.json       # Database template (copy to data.json)
│   ├── requirements.txt       # Python dependencies
│   └── start_server.vbs       # VBS script for hidden background launch
│
├── video-transcriber-frontend/
│   ├── src/
│   │   ├── main.jsx           # React entry point with AuthProvider wrapper
│   │   ├── App.jsx            # Main app: auth page + transcribe page + loading state
│   │   ├── AuthContext.jsx    # Auth state management (login/register/logout)
│   │   ├── App.css            # Styles: auth forms, transcribe UI, results, layout
│   │   └── index.css          # Global base styles (reset, fonts, background)
│   ├── index.html             # HTML entry point
│   ├── vite.config.js         # Vite config with /api proxy to backend
│   ├── package.json           # Node dependencies
│   └── assets/                # Static assets (favicon, etc.)
│
├── opendesign/
│   ├── index.html             # OpenDesign design viewer
│   └── manifest.json          # Design system manifest
│
├── start.bat                  # One-click launcher for both servers (Windows)
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
└── LICENSE                    # (optional)
```

---

## Author

Created and maintained by `daxler_boi`.
