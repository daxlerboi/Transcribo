@echo off
cd /d "%~dp0"
start /b "" uvicorn main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 600
echo Server started on http://localhost:8000
