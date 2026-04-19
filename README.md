# VoiceGuard - Deepfake Audio Detector

A real-time web application that detects AI-generated (deepfake) audio in phone calls and live conversations. Used to classify audio as real or synthetic with per-chunk analysis and automatic termination on detection.


<img width="1244" height="1017" alt="image" src="https://github.com/user-attachments/assets/fe6301a4-822a-431e-8e1c-4786fbf1e7df" />

## Features

Real-time Processing
- Analyzes 3-second audio chunks in real-time via WebSocket
- Instant REAL/FAKE classification with confidence scores
- Live confidence trend visualization

Intelligent Detection
- Confidence threshold: 80% for flagged detections
- Automatic call termination: Triggered after 2 consecutive high-confidence fake detections

User Interface
- Vanilla JavaScript frontend (no React/frameworks)
- Real-time waveform visualization
- Threat level gauge showing live detection status
- Call history with full chunk-by-chunk analysis
- File upload capability for batch analysis

## Quick Start

### Prerequisites

- Python 3.10 or higher
- FFmpeg (for audio format conversion)
  - Windows: choco install ffmpeg or download from https://ffmpeg.org
  - macOS: brew install ffmpeg
  - Linux: sudo apt-get install ffmpeg

### Local Installation

1. Clone and navigate to project

```bash
git clone https://github.com/ArthAgrawal/Deepfake_Audio.git
cd Deepfake_Audio
```

2. Install Python dependencies

```bash
cd deepfake_detector
pip install -r requirements.txt
```

3. Configure environment (optional)

```bash
cp .env.example .env
```

Edit .env to specify FFmpeg path if not in system PATH.

4. Run the server

**Windows:**
```bash
set PYTHONIOENCODING=utf-8
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Linux/macOS:**
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

5. Open in browser

```
http://localhost:8000
```

## How It Works

### Architecture

Frontend (Browser) -> WebSocket -> Backend (FastAPI) -> Model -> Results

### Processing Flow

File Upload Path
1. User selects audio file from disk
2. File sent to /analyze endpoint
3. FFmpeg converts to WAV (16kHz, mono)
4. Model processes full audio
5. Returns verdict (REAL/FAKE) and confidence percentage
6. Results displayed immediately

Live Recording Path
1. User starts recording via browser
2. Browser captures audio using MediaRecorder API
3. Audio split into 3-second chunks
4. Each chunk sent via WebSocket to backend
5. Backend receives, converts format, runs inference
6. Model outputs: verdict, confidence, fake_score, real_score
7. Results streamed back to frontend in real-time
8. Threat gauge updates live
9. Streak counter increments on consecutive fakes
10. Call auto-terminates when fake_streak reaches 2

### Detection Termination Logic

Termination Threshold: fake_score >= 80%
Consecutive Detections Required: 2 chunks
Auto-Terminate: Cuts call and sends cut_call: true to frontend

Example: If chunk 1 is fake (85% confidence) and chunk 2 is fake (92% confidence), call terminates immediately.

Streak Reset: If any chunk is classified as REAL, fake_streak resets to 0.

## Project Structure

```
Deepfake_Audio/
├── deepfake_detector/
│   ├── main.py                    # FastAPI application
│   ├── static/
│   │   └── index.html            # Web interface
│   ├── requirements.txt           # Python dependencies
│   ├── .env.example              # Configuration template
│   └── .env                      # Configuration (create from .env.example)
├── Dockerfile                     # Docker container definition
├── README.md                      # This file
└── LICENSE                        # MIT License
```


## Deployment

### Docker Deployment

Build image:
```bash
docker build -t deepfake-detector .
```

Run container:
```bash
docker run -p 8000:8000 -e FFMPEG_PATH=/usr/bin/ffmpeg deepfake-detector
```

### Hugging Face Spaces

1. Go to https://huggingface.co/new-space
2. Create space with Docker SDK
3. Link GitHub repository: https://github.com/ArthAgrawal/Deepfake_Audio
4. HF Spaces auto-deploys from Dockerfile
5. Public URL generated automatically


## API Endpoints

REST Endpoint: /analyze

Method: POST
Input: audio/wav file
Output: JSON with verdict, confidence, real_score, fake_score

WebSocket Endpoint: /ws

Method: WebSocket
Input: JSON chunks with base64 audio data
Output: Streaming JSON results with chunk_idx, verdict, confidence, fake_streak, cut_call

## Troubleshooting

Issue: "FFmpeg not found"
Solution: Install FFmpeg or set FFMPEG_PATH in .env

Issue: "Port already in use"
Solution: Kill existing Python processes or specify different port:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

Issue: "UnicodeEncodeError on Windows"
Solution: Set environment variable before running:
```bash
set PYTHONIOENCODING=utf-8
```

Issue: "WebSocket connection fails"
Solution: Check firewall allows WebSocket connections. Ensure server is running on correct port.

Issue: "Model download fails"
Solution: Ensure internet connection. First run downloads model from Hugging Face (300MB+). Can take 1-2 minutes.

Issue: "Slow inference on GPU"
Solution: Ensure PyTorch is installed for your GPU type:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## Configuration

Environment Variables (.env file):

FFMPEG_PATH: Path to FFmpeg executable (auto-detected if not set)
HOST: Server host (default: 0.0.0.0)
PORT: Server port (default: 8000)

## Performance

CPU Mode: 0.5-1.0 seconds per chunk
GPU Mode: 0.2-0.3 seconds per chunk (with CUDA-compatible PyTorch)
Memory: 2-3 GB for model loading
Disk: 300-400 MB for model download and cache

## Browser Support

Chrome/Chromium: Full support
Firefox: Full support
Safari: Full support
Edge: Full support

Requires browser support for:
- WebSocket API
- MediaRecorder API
- HTMLCanvasElement

## Technical Stack

Backend: FastAPI, Uvicorn, Python 3.10+
ML Framework: PyTorch, Transformers (Hugging Face)
Audio Processing: Librosa, FFmpeg
Frontend: Vanilla JavaScript, HTML5, Canvas API
Containerization: Docker

## License

MIT License - See LICENSE file for details

## Contributing

Issues and pull requests welcome.

## Citation

Model: Gustking/wav2vec2-large-xlsr-deepfake-audio-classification on Hugging Face Hub
Framework: PyTorch Transformers library

## Support

For issues, questions, or suggestions, open a GitHub issue.

---

Last Updated: April 2026
