import os
import re
import json
import urllib.request, urllib.error
import tempfile
import subprocess
import urllib.parse
import base64
import requests
from ipaddress import ip_address, ip_network
from fastapi import HTTPException
from youtube_transcript_api import YouTubeTranscriptApi

WHISPER_ENABLED = os.getenv("WHISPER_ENABLED", "1") == "1"
_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if not WHISPER_ENABLED:
        return None
    if _whisper_model is None:
        try:
            import whisper
            _whisper_model = whisper.load_model("base")
        except (ImportError, Exception):
            _whisper_model = False
    return _whisper_model if _whisper_model is not False else None

AUDIO_EXTS = {".m4a", ".mp3", ".wav", ".webm", ".ogg"}
YT_API = YouTubeTranscriptApi()

COOKIES_B64 = os.getenv("YOUTUBE_COOKIES", "")

PRIVATE_NETS = [
    ip_network("127.0.0.0/8"),
    ip_network("10.0.0.0/8"),
    ip_network("172.16.0.0/12"),
    ip_network("192.168.0.0/16"),
    ip_network("169.254.0.0/16"),
    ip_network("::1/128"),
]

def validate_url(url: str):
    if not url or len(url) > 2048:
        raise HTTPException(400, "URL is empty or too long")
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(400, "Only http/https URLs are allowed")
    if not parsed.netloc:
        raise HTTPException(400, "Invalid URL — missing hostname")
    if parsed.scheme == "file":
        raise HTTPException(400, "file:// URLs are not allowed")
    try:
        host = parsed.hostname
        if host:
            addr = ip_address(host)
            for net in PRIVATE_NETS:
                if addr in net:
                    raise HTTPException(400, "Internal/private IP addresses are not allowed")
    except ValueError:
        pass

def extract_video_id(url: str) -> str | None:
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([a-zA-Z0-9_-]{11})", url)
    return m.group(1) if m else None

def detect_platform(url: str) -> str:
    url_lower = url.lower()
    if re.search(r"(youtube\.com|youtu\.be)", url_lower):
        return "youtube"
    if re.search(r"(instagram\.com)", url_lower):
        return "instagram"
    return "unknown"

PREFERRED_LANGS = ["en", "hi", "es", "ar", "pt", "fr", "de", "ja", "ru", "ko", "zh-Hans", "zh-Hant"]

def _make_youtube_session() -> requests.Session | None:
    """Build a requests.Session with YouTube cookies from the env var."""
    if not COOKIES_B64:
        return None
    try:
        raw = json.loads(base64.b64decode(COOKIES_B64).decode())
        session = requests.Session()
        for c in raw:
            if isinstance(c, dict) and "domain" in c and "name" in c and "value" in c:
                session.cookies.set(
                    c["name"], c["value"],
                    domain=c["domain"].lstrip("."),
                    path=c.get("path", "/"),
                )
        return session
    except Exception:
        return None

def _fetch_transcript_with_cookies(video_id: str) -> dict | None:
    """Scrape ytInitialPlayerResponse from YouTube page using an authenticated session."""
    session = _make_youtube_session()
    if not session:
        return None
    try:
        resp = session.get(
            f"https://www.youtube.com/watch?v={video_id}",
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            },
            timeout=20,
        )
        if resp.status_code != 200:
            return None
        m = re.search(r'ytInitialPlayerResponse\s*=\s*({.*?});', resp.text, re.DOTALL)
        if not m:
            return None
        player = json.loads(m.group(1))
        tracks = (
            player.get("captions", {})
            .get("playerCaptionsTracklistRenderer", {})
            .get("captionTracks", [])
        )
        if not tracks:
            return None
        track = next((t for t in tracks if t.get("languageCode", "").startswith("en")), tracks[0])
        base_url = track["baseUrl"]
        if "fmt=" not in base_url:
            base_url += "&fmt=json"
        tr_resp = session.get(base_url, timeout=15)
        tr_data = tr_resp.json()
        segments = []
        for event in tr_data.get("events", []):
            start = event.get("tStartMs", 0) / 1000.0
            segs = event.get("segs", [])
            text = " ".join(s.get("utf8", "") for s in segs if isinstance(s, dict))
            if text.strip():
                duration = event.get("dDurationMs", 2000) / 1000.0
                segments.append({
                    "start": round(start, 2),
                    "end": round(start + duration, 2),
                    "text": text.strip(),
                })
        if not segments:
            return None
        full_text = " ".join(s["text"] for s in segments)
        return {"text": full_text, "segments": segments, "language": track.get("languageCode", "en")}
    except Exception:
        return None

def _fetch_transcript_fallback(video_id: str) -> dict | None:
    try:
        url = f"https://youtubetranscript.com/api?vid={video_id}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        if not data or not isinstance(data, list):
            return None
        segments = [
            {"start": round(s["start"], 2), "end": round(s["start"] + s["duration"], 2), "text": s["text"].strip()}
            for s in data if isinstance(s, dict)
        ]
        if not segments:
            return None
        text = " ".join(s["text"] for s in segments)
        return {"text": text, "segments": segments, "language": "en"}
    except Exception:
        return None

def get_youtube_transcript(video_id: str) -> dict | None:
    result = _fetch_transcript_with_cookies(video_id)
    if result is not None:
        return result
    for lang in (None, *PREFERRED_LANGS):
        try:
            kwargs = {"languages": [lang]} if lang else {}
            transcript = YT_API.get_transcript(video_id, **kwargs)
            if not transcript:
                continue
            segments = [
                {"start": round(s["start"], 2), "end": round(s["start"] + s["duration"], 2), "text": s["text"].strip()}
                for s in transcript
            ]
            text = " ".join(s["text"] for s in segments)
            return {"text": text, "segments": segments, "language": lang or "en"}
        except Exception:
            continue
    fallback = _fetch_transcript_fallback(video_id)
    if fallback:
        return fallback
    if COOKIES_B64:
        raise HTTPException(404, "No captions found for this video — music videos and shorts often lack captions. Try a video with dialogue (talks, tutorials, news).")
    raise HTTPException(502, (
        "YouTube blocked this server's IP. To fix this, "
        "export your YouTube cookies as JSON from your browser, "
        "base64-encode them, and set as YOUTUBE_COOKIES env var. "
        "Or run locally with 'start.bat'."
    ))

def download_audio(url: str) -> str:
    out_dir = tempfile.mkdtemp(prefix="transcribe_")
    try:
        out_template = os.path.join(out_dir, "%(title)s.%(ext)s")
        result = subprocess.run(
            [
                "yt-dlp",
                "-f", "worstaudio",
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "5",
                "--no-playlist",
                "--no-warnings",
                "-o", out_template,
                url,
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp failed: {result.stderr[:500]}")
        for f in os.listdir(out_dir):
            if any(f.lower().endswith(ext) for ext in AUDIO_EXTS):
                audio_path = os.path.join(out_dir, f)
                return audio_path
        raise RuntimeError("No audio file extracted from the URL")
    except Exception:
        _cleanup_dir(out_dir)
        raise

def _cleanup_dir(d):
    try:
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
        os.rmdir(d)
    except Exception:
        pass

def transcribe_audio(audio_path: str) -> dict:
    model = get_whisper_model()
    if not model:
        raise HTTPException(503, "Whisper speech-to-text is not available on this server. Only YouTube videos with captions are supported.")
    result = model.transcribe(audio_path)
    return {
        "text": result["text"].strip(),
        "segments": [
            {
                "start": round(s["start"], 2),
                "end": round(s["end"], 2),
                "text": s["text"].strip(),
            }
            for s in result["segments"]
        ],
    }

def process_url(url: str) -> dict:
    platform = detect_platform(url)
    if platform == "youtube":
        video_id = extract_video_id(url)
        if video_id:
            transcript = get_youtube_transcript(video_id)
            if transcript:
                return {"platform": platform, "url": url, **transcript}
            raise HTTPException(404, "No captions found for this video.")
    audio_path = download_audio(url)
    try:
        result = transcribe_audio(audio_path)
        result["platform"] = platform
        result["url"] = url
        return result
    finally:
        _cleanup_dir(os.path.dirname(audio_path))
