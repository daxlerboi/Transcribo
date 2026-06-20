import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from transcriber import process_url, validate_url
from auth import router as auth_router

ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
]

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
