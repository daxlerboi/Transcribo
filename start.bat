@echo off
echo Building frontend...
cd /d "%~dp0video-transcriber-frontend"
call npm run build
cd /d "%~dp0backend"
echo Starting Transcribo on http://localhost:8000
uvicorn main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 600