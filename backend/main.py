import os
import asyncio
import tempfile
import shutil
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from transcriber import process_url, validate_url, transcribe_audio
from auth import router as auth_router, get_current_user

AUDIO_EXTS = {".m4a", ".mp3", ".wav", ".webm", ".ogg", ".mp4", ".mov", ".avi", ".mkv"}
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB

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

from database import find_many, find_one, insert_one, update_one, delete_one

class TranscribeRequest(BaseModel):
    url: str

class TranscribeResponse(BaseModel):
    text: str
    platform: str
    url: str
    segments: list[dict]

@app.post("/api/transcribe", response_model=TranscribeResponse)
async def transcribe(req: TranscribeRequest, user: dict = Depends(get_current_user)):
    validate_url(req.url)
    try:
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, process_url, req.url),
            timeout=600,
        )
        title = result.get("segments", [{}])[0].get("text", req.url)[:80]
        await insert_one("transcriptions", {
            "user_email": user["email"],
            "title": title,
            "url": req.url,
            "platform": result["platform"],
            "text": result["text"],
            "segments": result["segments"],
        })
        return result
    except asyncio.TimeoutError:
        raise HTTPException(408, "Transcription timed out")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e)[:500])

@app.get("/api/history")
async def list_history(user: dict = Depends(get_current_user)):
    items = await find_many("transcriptions", {"user_email": user["email"]}, sort_by="created_at", reverse=True)
    return [
        {
            "id": t["_id"],
            "title": t.get("title", t["url"]),
            "url": t["url"],
            "platform": t["platform"],
            "created_at": t["created_at"],
        }
        for t in items
    ]

class RenameRequest(BaseModel):
    title: str

@app.patch("/api/history/{item_id}/title")
async def rename_history(item_id: str, req: RenameRequest, user: dict = Depends(get_current_user)):
    item = await find_one("transcriptions", {"_id": item_id, "user_email": user["email"]})
    if not item:
        raise HTTPException(404, "Not found")
    await update_one("transcriptions", {"_id": item_id}, {"title": req.title.strip()[:120]})
    return {"ok": True}

@app.delete("/api/history/{item_id}")
async def delete_history(item_id: str, user: dict = Depends(get_current_user)):
    item = await find_one("transcriptions", {"_id": item_id, "user_email": user["email"]})
    if not item:
        raise HTTPException(404, "Not found")
    await delete_one("transcriptions", {"_id": item_id})
    return {"ok": True}

@app.get("/api/history/{item_id}")
async def get_history(item_id: str, user: dict = Depends(get_current_user)):
    item = await find_one("transcriptions", {"_id": item_id, "user_email": user["email"]})
    if not item:
        raise HTTPException(404, "Not found")
    return {
        "id": item["_id"],
        "title": item.get("title", item["url"]),
        "url": item["url"],
        "platform": item["platform"],
        "text": item["text"],
        "segments": item["segments"],
        "created_at": item["created_at"],
    }

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/transcribe-file")
async def transcribe_file(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    if ext not in AUDIO_EXTS:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(AUDIO_EXTS))}")
    tmpdir = tempfile.mkdtemp(prefix="upload_")
    try:
        out_path = os.path.join(tmpdir, f"audio{ext}")
        with open(out_path, "wb") as f:
            while True:
                chunk = await file.read(8 * 1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                if os.path.getsize(out_path) > MAX_FILE_SIZE:
                    raise HTTPException(413, "File too large — max 1GB")
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, transcribe_audio, out_path),
            timeout=600,
        )
        title = result.get("segments", [{}])[0].get("text", file.filename or "untitled")[:80]
        await insert_one("transcriptions", {
            "user_email": user["email"],
            "title": title,
            "url": f"file:{file.filename}",
            "platform": "local",
            "text": result["text"],
            "segments": result["segments"],
        })
        result["platform"] = "local"
        result["url"] = f"file:{file.filename}"
        return result
    except asyncio.TimeoutError:
        raise HTTPException(408, "Transcription timed out")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e)[:500])
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

FRONTEND_DIR = Path(os.getenv("FRONTEND_DIR", str(Path(__file__).resolve().parent.parent / "video-transcriber-frontend" / "dist")))
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
