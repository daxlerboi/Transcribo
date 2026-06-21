FROM python:3.13-slim

WORKDIR /app

# Install Node.js for frontend build + ffmpeg for yt-dlp
RUN apt-get update && apt-get install -y nodejs npm ffmpeg && rm -rf /var/lib/apt/lists/*

# Build frontend
COPY video-transcriber-frontend/package.json video-transcriber-frontend/package-lock.json* ./video-transcriber-frontend/
RUN cd video-transcriber-frontend && npm install
COPY video-transcriber-frontend/ ./video-transcriber-frontend/
RUN cd video-transcriber-frontend && npm run build

# Install backend deps
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt
COPY backend/ ./backend/

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "600"]
