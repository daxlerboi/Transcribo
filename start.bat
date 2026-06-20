@echo off
echo Starting Transcribo backend...
start "Transcribo Backend" cmd /c "cd /d D:\My_Web_Tools\video-transcriber\backend && uvicorn main:app --host 127.0.0.1 --port 8000 --timeout-keep-alive 600"
echo Starting Transcribo frontend...
start "Transcribo Frontend" cmd /c "cd /d D:\My_Web_Tools\video-transcriber\video-transcriber-frontend && npm run dev"
echo.
echo Open http://localhost:5173
