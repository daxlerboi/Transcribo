import os
import re
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
        except Exception:
            _whisper_model = False
    return _whisper_model if _whisper_model is not False else None

AUDIO_EXTS = {".m4a", ".mp3", ".wav", ".webm", ".ogg"}
YT_API = YouTubeTranscriptApi()

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

def get_youtube_transcript(video_id: str) -> dict | None:
    try:
        transcript_list = YT_API.list(video_id)
        available = {t.language_code for t in transcript_list}
        chosen_lang = None
        for lang in PREFERRED_LANGS:
            if lang in available:
                chosen_lang = lang
                break
        if not chosen_lang and available:
            chosen_lang = sorted(available)[0]
        if not chosen_lang:
            return None
        transcript = YT_API.fetch(video_id, [chosen_lang])
        segments = [
            {"start": round(s.start, 2), "end": round(s.start + s.duration, 2), "text": s.text.strip()}
            for s in transcript
        ]
        text = " ".join(s["text"] for s in segments)
        return {"text": text, "segments": segments, "language": chosen_lang}
    except Exception:
        return None

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
    audio_path = download_audio(url)
    try:
        result = transcribe_audio(audio_path)
        result["platform"] = platform
        result["url"] = url
        return result
    finally:
        _cleanup_dir(os.path.dirname(audio_path))
