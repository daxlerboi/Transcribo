# Transcribo

[![React](https://img.shields.io/badge/React-20232A?logo=react&logoColor=61DAFB)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white)](https://vite.dev/)
[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Whisper](https://img.shields.io/badge/Whisper-OpenAI-412991)](https://github.com/openai/whisper)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-powered-FF0000?logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)
[![Windows](https://img.shields.io/badge/Windows-supported-0078D4?logo=windows&logoColor=white)](https://www.microsoft.com/windows)

Built by `daxler_boi`

Transcribo is a full-stack video transcription web app. Paste a YouTube/Instagram link or upload a local audio/video file — get the full transcript with timestamped segments.

---

## What It Does

- **YouTube transcripts** — Fetches existing captions instantly via YouTube's API. No download. No GPU.
- **Instagram + other platforms** — Falls back to yt-dlp + OpenAI Whisper for any video URL.
- **Local file upload** — Upload MP3, MP4, WAV, WebM, MOV, AVI, MKV and transcribe with Whisper locally.
- **Multi-language** — Auto-detects available caption languages across 12 languages, picks the best match.
- **Timestamped segments** — Returns the full transcript plus individual segments with start/end times.
- **History sidebar** — ChatGPT-style panel on the left. Auto-saves every transcription. Rename, delete, or re-open past results.
- **Copy to clipboard** — One-click copy of the full transcript text.
- **User authentication** — Register, login, logout with JWT-based sessions. Server-side token blacklist on logout.
- **Security-first** — SSRF guard, URL validation, temp file cleanup, stdlib hashing (no legacy deps).

---

## How It Is Built

The project follows a single-service architecture:

1. **React frontend** is built to static files (`dist/`) via Vite.
2. **FastAPI backend** serves both the API routes and the built frontend from one port.
3. No separate dev server needed in production — just run `start.bat` and open `http://localhost:8000`.

The frontend handles three states: loading (token validation), auth page (login/register), and transcribe page (the main interface with URL input, file upload, and history sidebar). The backend handles URL validation, platform detection, language selection, file transcription, and transcription orchestration.

**Auth is pure Python stdlib** — no passlib, no bcrypt, no python-jose. Uses `hashlib.pbkdf2_hmac` for password hashing and `hmac` + `base64` for JWT signing. This means zero C-extension build failures and full Python 3.14 compatibility.

**Database is a JSON file** — no MongoDB, no SQLite, no server process. All data lives in `backend/data.json`, auto-created on first write.

---

## Tech Stack

### Frontend
- **React 19** — UI framework
- **Vite 8** — Build tool and dev server
- **CSS** — Plain CSS (no framework, no dependencies)
- **Icons** — Inline SVG components (waveform, YouTube, Instagram, hamburger, trash, plus)

### Backend
- **Python 3.13+** — Runtime
- **FastAPI** — REST API framework (async)
- **stdlib only for auth** — `hashlib.pbkdf2_hmac` (password hashing), `hmac` + `base64` (JWT)
- **youtube-transcript-api** — Fetch existing YouTube captions (instant)
- **yt-dlp** — Download audio from YouTube/Instagram
- **OpenAI Whisper** — Speech-to-text (fallback for non-caption videos + file uploads)
- **Uvicorn** — ASGI server

### Database
- **JSON file** (`backend/data.json`) — Single-file storage, auto-created, zero config. No database server needed.

---

## Architecture Overview

```
User's Browser
      │
      ▼
FastAPI Backend (localhost:8000)
  Serves: built React frontend + API routes
      │
      ├── Auth System ──► JSON file (data.json)
      │      ├─ POST /api/auth/register
      │      ├─ POST /api/auth/login
      │      ├─ POST /api/auth/logout
      │      └─ GET  /api/auth/me
      │
      ├── Transcription (URL)
      │      ├─ YouTube ──► YouTube Transcript API (instant)
      │      │              └─► youtubetranscript.com (fallback)
      │      │              └─► requests.Session with cookies (last resort)
      │      └─ Instagram ──► yt-dlp + Whisper (download + transcribe)
      │
      ├── Transcription (File Upload)
      │      └─ Upload ──► Save to temp dir ──► Whisper transcribe
      │
      └── History
             ├─ GET    /api/history
             ├─ GET    /api/history/{id}
             ├─ PATCH  /api/history/{id}/title
             └─ DELETE /api/history/{id}
```

The frontend is pre-built (`npm run build`) and served as static files by FastAPI. API routes are registered first, then the catch-all static file mount serves the frontend for any non-API path.

---

## Code Walkthrough

### Backend

#### `backend/main.py`
The FastAPI application entry point.

- Creates the FastAPI app with CORS middleware
- Includes the auth router (`/api/auth/*`)
- Defines `/api/transcribe` — accepts `{ "url": "..." }`, validates URL, runs transcription pipeline with 10-minute timeout
- Defines `/api/transcribe-file` — accepts multipart file upload, saves to temp dir, transcribes with Whisper
- Defines history CRUD endpoints (`/api/history/*`)
- Serves built frontend from `../video-transcriber-frontend/dist/`
- `/api/health` — health check

```python
# Heavy transcription runs in a thread pool to not block the event loop
result = await asyncio.wait_for(
    asyncio.get_event_loop().run_in_executor(None, process_url, req.url),
    timeout=600,
)
```

#### `backend/auth.py`
Authentication system with pure-stdlib JWT.

- **Register** (`POST /api/auth/register`) — Validates email + password (min 6 chars), checks duplicates, hashes password with `hashlib.pbkdf2_hmac`, stores user, returns JWT token
- **Login** (`POST /api/auth/login`) — Finds user by email, verifies password hash, returns JWT token
- **Logout** (`POST /api/auth/logout`) — Adds current token to a blacklist stored on the user document
- **Me** (`GET /api/auth/me`) — Returns the authenticated user's info
- **JWT creation** — Tokens contain `sub` (email) and `exp` (7 days), signed with HMAC-SHA256 using `hmac` + `base64`
- **Auth middleware** — `get_current_user()` dependency decodes JWT, looks up user, checks token blacklist

No external auth libraries. Everything uses `hashlib`, `hmac`, `base64`, `json`, `secrets`, and `uuid` from Python's standard library.

#### `backend/transcriber.py`
The core transcription engine.

- **`validate_url(url)`** — Security filter: checks URL is not empty and under 2048 chars, only allows `http`/`https` schemes, rejects private/internal IP addresses (SSRF guard)
- **`process_url(url)`** — Orchestrator: detects platform, for YouTube tries the transcript pipeline, for everything else downloads audio + Whisper
- **YouTube pipeline:**
  1. `_fetch_transcript_with_cookies()` — Uses `requests.Session()` with cookies from `YOUTUBE_COOKIES` env var to scrape `ytInitialPlayerResponse` from YouTube page
  2. `YouTubeTranscriptApi().fetch()` — Tries 12 languages in preference order
  3. `_fetch_transcript_fallback()` — Queries `youtubetranscript.com` API
- **`download_audio(url)`** — Uses yt-dlp to download worst-quality audio, converts to MP3. Creates temp directory, cleans up on both success and failure.
- **`transcribe_audio(audio_path)`** — Loads Whisper `base` model, transcribes audio, returns text + segments
- **Cookie bypass** — If YouTube blocks the server IP, set `YOUTUBE_COOKIES` env var to base64-encoded JSON cookies from your browser

#### `backend/database.py`
JSON file database abstraction.

- Stores everything in `backend/data.json`
- Auto-creates file on first write if it doesn't exist
- Methods: `find_one()`, `insert_one()`, `update_one()`, `delete_one()`, `find_many()`
- All methods are async, called with `await` throughout auth and history routes
- Auto-assigns UUIDs for `_id`, timestamps for `created_at`
- Writes to disk after every mutation (atomic for single-process use)

Methods:
```python
find_one(collection, query)           # Returns first matching doc or None
insert_one(collection, doc)           # Returns doc with auto-assigned _id
update_one(collection, query, update) # Returns True/False
delete_one(collection, query)         # Returns True/False
find_many(collection, query, sort_by, reverse)  # Returns list of docs
```

#### `backend/requirements.txt`
```
fastapi>=0.115
uvicorn>=0.32
yt-dlp>=2024.12
youtube-transcript-api>=0.6
pydantic>=2.0
python-multipart>=0.0.18
python-dotenv>=1.0
```

No C-extension dependencies. Pure Python only. No passlib, no bcrypt, no python-jose, no pymongo, no motor, no cryptography.

---

### Frontend

#### `video-transcriber-frontend/src/main.jsx`
React entry point. Wraps the entire app in `AuthProvider` to make auth state available everywhere.

#### `video-transcriber-frontend/src/App.jsx`
Main application component. Contains three logical views:

1. **Loading screen** — Shown while checking if an existing JWT token is still valid
2. **Auth page** — Login or Register form with error display and mode switching
3. **Transcribe page** — The main interface:
   - Header with app name, hamburger menu (sidebar toggle), user email, logout button
   - URL input + Transcribe button
   - File upload dropzone + Transcribe file button
   - Error display area
   - Results section: platform badge, full transcript, timestamped segments, copy button
   - History sidebar (slides in from left)

Key components:
- `AuthPage` — Login/register form with email + password inputs, submit, error display
- `Sidebar` — History panel with new-chat button, scrollable list of past transcriptions, delete button per item
- `TranscribePage` — Main interface orchestrating URL transcription, file upload, history management

Inline SVG icons: WaveIcon, YouTubeIcon, InstagramIcon, HamburgerIcon, PlusIcon, TrashIcon

#### `video-transcriber-frontend/src/AuthContext.jsx`
React context for authentication state management.

- **State**: `user`, `token`, `loading`
- **On mount**: Checks localStorage for token, validates against `/api/auth/me`, clears invalid tokens
- **`login(email, password)`**: POST to `/api/auth/login`, stores token, sets user
- **`register(email, password)`**: POST to `/api/auth/register`, stores token, sets user
- **`logout()`**: POST to `/api/auth/logout`, clears token and user state

#### `video-transcriber-frontend/src/App.css`
Complete styling for the entire application (~675 lines). Covers:
- App layout with sidebar + main content area
- Header with brand, user info, logout
- URL input + Transcribe button with focus rings and hover states
- File upload dropzone with dashed border and selected file display
- Loading spinner and progress bar animations
- Error message styling (red card)
- Result cards with platform badges (YouTube orange, Instagram pink, local green)
- Transcript full text and timestamped segments list
- Auth page (centered card layout with form inputs)
- Sidebar (dark panel, slide-in animation, overlay)
- History items with hover delete button
- Responsive breakpoint at 900px

#### `video-transcriber-frontend/vite.config.js`
Vite configuration with API proxy for development. Proxies `/api/*` requests to FastAPI on port 8000 with 10-minute timeout.

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
      ├── Register: checks duplicates, hashes password (pbkdf2_hmac), stores user
      └── Login: finds user, verifies password hash
      │
      ▼
Backend creates JWT token (HMAC-SHA256, 7-day expiry)
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

## Transcription Pipeline (YouTube)

```
User pastes YouTube URL
      │
      ▼
URL validation — scheme, length, SSRF guard
      │
      ▼
extract_video_id() — regex for v= / youtu.be/ / shorts/
      │
      ▼
1. _fetch_transcript_with_cookies()
   └── requests.Session() with YOUTUBE_COOKIES
       └── Scrapes ytInitialPlayerResponse from YouTube page
           └── Parses caption tracks, fetches in JSON format
      │
      (if fails)
      ▼
2. YouTubeTranscriptApi().fetch()
   └── Tries 12 languages in preference order
      │
      (if fails)
      ▼
3. _fetch_transcript_fallback()
   └── Queries youtubetranscript.com API
      │
      (if all fail)
      ▼
Returns error — explains how to fix (cookies or local)
```

## Transcription Pipeline (File Upload)

```
User selects file + clicks "Transcribe file"
      │
      ▼
File extension validated (.mp3, .mp4, .wav, .webm, .ogg, .mov, .avi, .mkv)
      │
      ▼
File saved to temp directory
      │
      ▼
Whisper base model transcribes audio
      │
      ▼
Returns text + timestamped segments
      │
      ▼
Temp directory cleaned up
Result saved to history
```

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
  "access_token": "eyJ...",
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
  "access_token": "eyJ...",
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

### Transcription Endpoints

#### `POST /api/transcribe`
Transcribe a video URL.

**Request:**
```json
{ "url": "https://youtu.be/dQw4w9WgXcQ" }
```

**Auth:** Required (Bearer token)

**Response (200):**
```json
{
  "text": "We're no strangers to love...",
  "platform": "youtube",
  "url": "https://youtu.be/dQw4w9WgXcQ",
  "segments": [
    { "start": 1.36, "end": 3.04, "text": "[music]" },
    { "start": 3.04, "end": 6.12, "text": "We're no strangers to love..." }
  ]
}
```

**Errors:** `400` (invalid URL), `408` (timeout), `502` (YouTube blocked), `500` (server error)

#### `POST /api/transcribe-file`
Transcribe an uploaded audio/video file.

**Request:** Multipart form with `file` field
- **Auth:** Required (Bearer token)
- **Accepted types:** `.mp3`, `.mp4`, `.m4a`, `.wav`, `.webm`, `.ogg`, `.mov`, `.avi`, `.mkv`
- **Max size:** 1GB

**Response (200):** Same format as `POST /api/transcribe` with `"platform": "local"`

### History Endpoints

#### `GET /api/history`
List all transcriptions for the authenticated user.
- **Auth:** Required (Bearer token)
- **Response (200):** Array of `{ id, title, url, platform, created_at }`

#### `GET /api/history/{id}`
Get a full transcription with text and segments.
- **Auth:** Required (Bearer token)
- **Response (200):** `{ id, title, url, platform, text, segments, created_at }`

#### `PATCH /api/history/{id}/title`
Rename a transcription.
- **Auth:** Required (Bearer token)
- **Request:** `{ "title": "New name" }`

#### `DELETE /api/history/{id}`
Delete a transcription.
- **Auth:** Required (Bearer token)

### Health Check

#### `GET /api/health`
- **Response (200):** `{ "status": "ok" }`

---

## Security Implementation

| # | Fix | File:Line |
|---|-----|-----------|
| 1 | **CORS locked down** — pinned to specific origins, not wide-open `["*"]` | `main.py` |
| 2 | **URL scheme validation** — Only `http`/`https` allowed. Blocks `file://`, `ftp://`, `data://` | `transcriber.py` |
| 3 | **URL length limit** — Capped at 2048 characters | `transcriber.py` |
| 4 | **SSRF guard** — Blocks private IP ranges: `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1/128` | `transcriber.py` |
| 5 | **Temp dir cleanup** — Every download/file upload gets an isolated temp dir, cleaned up on both success and error | `transcriber.py` |
| 6 | **Password hashing** — PBKDF2-HMAC-SHA256 with random salt | `auth.py` |
| 7 | **JWT token blacklist** — Logout adds token to server-side blacklist, checked on every authenticated request | `auth.py` |
| 8 | **File type validation** — Only accepted audio/video extensions allowed for upload | `main.py` |
| 9 | **File size limit** — 1GB max upload size enforced during streaming write | `main.py` |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET` | `dev-secret` | Secret for signing JWT tokens (change in production) |
| `YOUTUBE_COOKIES` | — | Base64-encoded JSON cookies from browser (bypass YouTube IP block) |
| `WHISPER_ENABLED` | `1` | Set to `0` to disable Whisper on low-memory servers |

---

## Setup & Running

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

**Option A — Production (single command):**
```bash
start.bat
```
Builds frontend, starts backend on `http://localhost:8000`. Open in browser.

**Option B — Development (two terminals, hot reload):**

Terminal 1 (Backend):
```bash
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Terminal 2 (Frontend):
```bash
cd video-transcriber-frontend
npm run dev
```

Open **http://localhost:5173** — Vite proxies `/api/*` to the backend.

### Production Deploy

```bash
cd video-transcriber-frontend
npm run build
cd ../backend
uvicorn main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 600
```

Visit **http://localhost:8000** — backend serves both API and built frontend.

---

## Project Structure

```
video-transcriber/
│
├── backend/
│   ├── main.py                # FastAPI server — CORS, routes, transcribe, file upload, history, static files
│   ├── auth.py                # Register, Login, Logout, /me — pure stdlib JWT (no passlib/jose)
│   ├── transcriber.py         # YouTube Transcript API + Whisper + cookie bypass + URL validation
│   ├── database.py            # JSON file database (find_one, insert_one, update_one, delete_one)
│   ├── data.json              # Database file (gitignored, auto-created on first write)
│   ├── data.sample.json       # Database template
│   ├── requirements.txt       # Python dependencies (pure Python, no C extensions)
│   ├── .env.example           # Environment variables template
│   └── serve.bat              # Background server launcher
│
├── video-transcriber-frontend/
│   ├── src/
│   │   ├── main.jsx           # React entry point with AuthProvider wrapper
│   │   ├── App.jsx            # Main app: auth page + transcribe page + sidebar + file upload
│   │   ├── AuthContext.jsx    # Auth state management (JWT in localStorage)
│   │   ├── App.css            # Styles: layout, header, inputs, results, sidebar, auth forms
│   │   └── index.css          # Global base styles (reset, font, background)
│   ├── index.html             # HTML entry point
│   ├── vite.config.js         # Vite config with /api proxy to backend (dev mode)
│   └── package.json           # Node dependencies
│
├── start.bat                  # One-click launcher: builds frontend, starts backend
├── .gitignore
└── README.md
```

---

## Platform Notes

- **Render deploy** — YouTube blocks Render's IP range. YouTube captions won't work from the cloud. Set `YOUTUBE_COOKIES` env var with browser cookies to bypass, or run locally with `start.bat`.
- **Whisper on Render** — Disabled by default (512MB RAM can't load 1.5GB model). Set `WHISPER_ENABLED=0` env var.
- **File upload on Render** — Won't work because Whisper is disabled. File upload + transcription only works locally.
- **All stdlib auth** — No external auth libraries. `hashlib` + `hmac` + `base64` only.
- **History** — Auto-saves every transcription to `data.json`. Sidebar shows all past transcriptions with rename and delete.

---

## Author

Created and maintained by `daxler_boi`.
