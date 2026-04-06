# VoiceGuard - Deepfake Audio Detector

A real-time web application that detects AI-generated (deepfake) audio in phone calls and live conversations.

**Live Detection Features:**
- 🎤 Real-time audio chunk analysis (3-second intervals)
- 🔴 Automatic call termination on 2 consecutive deepfake detections
- 📊 Live confidence trend chart
- 🎯 Per-chunk verdict with confidence scores
- 📋 Call summary with full analysis history

---

## Quick Start

### Local Development

1. **Install dependencies**
   ```bash
   cd deepfake_detector
   pip install -r requirements.txt
   ```

2. **Setup environment**
   ```bash
   cp .env.example .env
   # Edit .env with FFmpeg path if needed
   ```

3. **Run server**
   ```bash
   # Linux/Mac
   bash run.sh
   
   # Windows
   run.bat
   
   # Or manually
   python -m uvicorn main:app --reload
   ```

4. **Open browser**
   ```
   http://localhost:8000
   ```

---

## Deploy Online

For public deployment (Railway, Render, Docker, etc.), see [DEPLOYMENT.md](DEPLOYMENT.md).

**Recommended:** Render.com with the included [Dockerfile](Dockerfile) and [render.yaml](render.yaml)

---

## Requirements

- **Python 3.10+**
- **FFmpeg** (for audio processing)
  - Windows: `choco install ffmpeg` or download from https://ffmpeg.org
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt-get install ffmpeg`

---

## Model Info

Uses Hugging Face model: **Gustking/wav2vec2-large-xlsr-deepfake-audio-classification**
- Architecture: Wav2Vec2 + Large XLSR
- Languages: Multilingual
- Training Data: ASVspoof 2021, other deepfake datasets
- Inference Speed: ~0.5s per 3-second chunk (CPU)

---

## How It Works

1. Browser captures 3-second audio chunks via WebSocket
2. Chunks converted to 16kHz WAV via FFmpeg
3. Model extracts features + classifies: REAL or FAKE
4. Results displayed in real-time with confidence %
5. After 2 consecutive high-confidence fakes → call terminated

---

## Project Structure

```
deepfake_detector/
  ├── main.py                 # FastAPI backend
  ├── static/
  │   └── index.html         # React-free frontend (vanilla JS)
  ├── requirements.txt       # Dependencies
  ├── .env.example          # Configuration template
  ├── run.sh / run.bat      # Startup scripts
  └── .env                  # (create from .env.example)
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "FFmpeg not found" | Install FFmpeg, update `FFMPEG_PATH` in `.env` |
| WebSocket connection fails | Check firewall allows WebSocket (port specified in logs) |
| Slow inference | Ensure CUDA installed if GPU available (`pip install torch --index-url https://download.pytorch.org/whl/cu118`) |

---

## License

MIT

---

## Next Steps

- [Deploy Guide](DEPLOYMENT.md)
- [Full Documentation](deepfake_detector/README.md)
