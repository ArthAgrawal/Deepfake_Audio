#!/bin/bash
# VoiceGuard Startup Script (Linux/Mac)

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠ .env file not found. Using defaults."
    echo "  Copy .env.example to .env and configure."
fi

# Ensure ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠ FFmpeg not found. Install with:"
    echo "  macOS: brew install ffmpeg"
    echo "  Ubuntu/Debian: sudo apt-get install ffmpeg"
    exit 1
fi

# Set defaults if not in .env
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}

echo "🚀 Starting VoiceGuard"
echo "   Host: $HOST"
echo "   Port: $PORT"
echo "   URL: http://localhost:$PORT"

# Run with uvicorn
python -m uvicorn main:app --host "$HOST" --port "$PORT" --workers 1
