# VoiceGuard - Deepfake Audio Detector
## Deployment Guide

### Quick Start (Local)

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run the Server**
   
   **Linux/Mac:**
   ```bash
   bash run.sh
   ```
   
   **Windows:**
   ```bash
   run.bat
   ```
   
   **Or manually:**
   ```bash
   python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```

4. **Access the App**
   Open: `http://localhost:8000`

---

### Prerequisites

- **Python 3.10+**
- **FFmpeg** (for audio processing)
  - Windows: Download from https://ffmpeg.org/download.html or use chocolatey: `choco install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt-get install ffmpeg`

---

### Deployment Options

#### 1. **Railway.app** (Recommended - Free Tier Available)
Zero-config deployment with environment variable support.

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

**Note:** Railway provides Linux containers, so FFmpeg will be available via apt-get.

#### 2. **Heroku**
```bash
# Install Heroku CLI, then:
heroku create voiceguard-detector
git push heroku main
```

Create `Procfile`:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

#### 3. **Render.com**
- Connect your GitHub repo
- Set `start command`: `python -m uvicorn main:app --host 0.0.0.0 --port 8000`
- Add environment variable: `FFMPEG_PATH=/usr/bin/ffmpeg`

#### 4. **Docker** (For Any Cloud)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY deepfake_detector/ .

# Expose port
EXPOSE 8000

# Run server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Then deploy to DockerHub, AWS ECS, Google Cloud Run, Azure Container Instances, etc.

#### 5. **DigitalOcean App Platform**
- Create app from GitHub repo
- Set build command: `pip install -r deepfake_detector/requirements.txt`
- Set run command: `cd deepfake_detector && python -m uvicorn main:app --host 0.0.0.0 --port 8080`
- Add `http_port: 8080` to app spec

---

### Environment Variables

Create a `.env` file (use `.env.example` as template):

```ini
# FFmpeg binary path
FFMPEG_PATH=/usr/bin/ffmpeg

# Server configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

**In cloud platforms**, set these via the dashboard:
- Railway: Variables tab
- Heroku: Config Vars
- Render: Environment
- Docker: Pass with `-e FFMPEG_PATH=/path/to/ffmpeg`

---

### Performance Tips

1. **Use CUDA** - GPU acceleration dramatically speeds up inference
   - Railway/Render: Not supported (CPU only)
   - Self-hosted: Install CUDA-compatible PyTorch
   - Check: `python -c "import torch; print(torch.cuda.is_available())"`

2. **Model Caching** - The model downloads on first startup (~1GB)
   - Subsequent runs use cached version
   - Keep containers alive to preserve cache

3. **Concurrent Requests** - Set `--workers` based on server capacity
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
   ```

---

### Production Security

For public deployment, add to `main.py`:

```python
# Rate limiting (install: pip install slowapi)
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.websocket("/ws")
@limiter.limit("10/minute")
async def websocket_endpoint(websocket: WebSocket):
    # ... existing code
```

Use HTTPS in production:
- Railway, Render, Heroku provide free HTTPS by default
- Self-hosted: Use nginx + Let's Encrypt

---

### Troubleshooting

| Error | Solution |
|-------|----------|
| FFmpeg not found | Install ffmpeg, set `FFMPEG_PATH` in `.env` |
| Model download fails | Check internet, increase timeout, or pre-download |
| WebSocket connection fails | Ensure server allows WebSocket (check firewall/proxy) |
| High memory usage | Reduce `--workers` or deploy with more RAM |
| Slow inference | Use GPU (CUDA) or optimize model quantization |

---

### Cost Estimates

| Platform | Free Tier | Notes |
|----------|-----------|-------|
| Railway | $5/month | Most generous free tier, includes 512MB RAM |
| Render | $7/month | Sleep after inactivity |
| Heroku | Deprecated | Recommend alternatives |
| DigitalOcean | $4/month | Droplet cost; add app platform fee |
| AWS | Pay-as-you-go | Free tier 750h/month (EC2 t2.micro) |

**Best Choice for Beginners:** Railway or Render

---

### Support

For issues or questions, check:
- FFmpeg docs: https://ffmpeg.org/documentation.html
- FastAPI docs: https://fastapi.tiangolo.com/
- Hugging Face model: https://huggingface.co/Gustking/wav2vec2-large-xlsr-deepfake-audio-classification
