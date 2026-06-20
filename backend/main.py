import os
import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from transcriber import process_url, validate_url
from auth import router as auth_router, get_current_user

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

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "video-transcriber-frontend" / "dist"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
