import os
import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from transcriber import process_url, validate_url
from auth import router as auth_router

ORIGINS = os.getenv("ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173").split(",")

app = FastAPI(title="Transcribo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

class TranscribeRequest(BaseModel):
    url: str

class TranscribeResponse(BaseModel):
    text: str
    platform: str
    url: str
    segments: list[dict]

@app.post("/api/transcribe", response_model=TranscribeResponse)
async def transcribe(req: TranscribeRequest):
    validate_url(req.url)
    try:
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, process_url, req.url),
            timeout=600,
        )
        return result
    except asyncio.TimeoutError:
        raise HTTPException(408, "Transcription timed out — the video may be too long")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e)[:500])

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/debug")
async def debug():
    import traceback, sys
    info = {"python": sys.version, "cwd": os.getcwd(), "files": os.listdir(".")}
    try:
        from database import find_one, _read
        data = _read()
        info["read_ok"] = True
        info["users_count"] = len(data.get("users", []))
    except Exception as e:
        info["error"] = str(e)
        info["traceback"] = traceback.format_exc()
    try:
        r = await find_one("users", {"email": "x@x.com"})
        info["find_one_result"] = r
    except Exception as e:
        info["find_one_error"] = str(e)
    return info

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "video-transcriber-frontend" / "dist"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
