import os
import re
import json
import urllib.request, urllib.error
import tempfile
import subprocess
import urllib.parse
from ipaddress import ip_address, ip_network
from fastapi import HTTPException
from youtube_transcript_api import YouTubeTranscriptApi

# Whisper is optional — disabled on low-memory environments (Render free tier, etc.)
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

def _extract_subs_ytdlp(video_id: str) -> dict | None:
    if not COOKIES_B64:
        return None
    import base64
    cookies_path = os.path.join(tempfile.gettempdir(), f"yt_cookies_{video_id}.txt")
    out_dir = tempfile.mkdtemp(prefix="subs_")
    try:
        with open(cookies_path, "wb") as f:
            f.write(base64.b64decode(COOKIES_B64))
        out_template = os.path.join(out_dir, "%(id)s")
        subprocess.run(
            [
                "yt-dlp", f"https://www.youtube.com/watch?v={video_id}",
                "--write-auto-subs", "--sub-lang", "en",
                "--skip-download", "--no-warnings",
                "--sub-format", "vtt",
                "--cookies", cookies_path,
                "-o", out_template,
            ],
            capture_output=True, text=True, timeout=60,
        )
        segments = []
        for f in os.listdir(out_dir):
            if f.endswith(".vtt"):
                with open(os.path.join(out_dir, f), encoding="utf-8") as sf:
                    content = sf.read()
                for block in content.strip().split("\n\n"):
                    lines = block.strip().split("\n")
                    if len(lines) >= 2 and "-->" in lines[0]:
                        start_str = lines[0].split(" --> ")[0].replace(",", ".")
                        parts = start_str.split(":")
                        start = int(parts[0])*3600 + int(parts[1])*60 + float(parts[2])
                        t = " ".join(lines[1:]).replace("<c>", "").replace("</c>", "").replace("&amp;", "&").strip()
                        if t:
                            segments.append({"start": round(start, 2), "end": round(start + 2, 2), "text": t})
        if segments:
            text = " ".join(s["text"] for s in segments)
            return {"text": text, "segments": segments, "language": "en"}
        return None
    except Exception:
        return None
    finally:
        try: os.remove(cookies_path)
        except: pass
        try: _cleanup_dir(out_dir)
        except: pass

def get_youtube_transcript(video_id: str) -> dict | None:
    last_error = None
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
        except Exception as e:
            last_error = e
            continue
    fallback = _fetch_transcript_fallback(video_id)
    if fallback:
        return fallback
    cookie_subs = _extract_subs_ytdlp(video_id)
    if cookie_subs:
        return cookie_subs
    msg = str(last_error)
    if "blocked" in msg.lower() or "ip" in msg.lower():
        if not COOKIES_B64:
            raise HTTPException(502, "YouTube blocked this server's IP. To bypass, export cookies from your browser and set YOUTUBE_COOKIES env var (base64-encoded cookies.txt). Or run locally with 'start.bat'.")
        raise HTTPException(502, "Cookies provided but still blocked by YouTube. Your cookies may be expired — re-export them from your browser.")
    raise HTTPException(502, msg.split("\n")[0]) from None

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
