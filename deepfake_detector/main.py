import asyncio
import base64
import json
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch
import torch.nn.functional as F
import librosa
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ─── FFmpeg ───────────────────────────────────────────────────────────────────

def resolve_ffmpeg() -> str:
    configured = os.getenv("FFMPEG_PATH", "").strip()
    candidates = [configured] if configured else []
    candidates += [
        "ffmpeg",
        r"C:\ffmpeg\ffmpeg-8.1-essentials_build\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        os.path.join(os.getenv("ProgramFiles", r"C:\Program Files"), "ffmpeg", "bin", "ffmpeg.exe"),
    ]
    for c in candidates:
        if not c:
            continue
        resolved = shutil.which(c)
        if resolved:
            return resolved
        if os.path.isfile(c):
            return c
    return "ffmpeg"

FFMPEG = resolve_ffmpeg()
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

try:
    subprocess.run([FFMPEG, "-version"], capture_output=True, check=True, timeout=5)
    logger.info(f"FFmpeg: {FFMPEG}")
except Exception:
    logger.warning(f"FFmpeg not found at '{FFMPEG}'. Audio processing will fail.")

# ─── Model ────────────────────────────────────────────────────────────────────

MODEL_NAME = "Gustking/wav2vec2-large-xlsr-deepfake-audio-classification"
logger.info(f"Loading model: {MODEL_NAME}")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
feature_extractor = AutoFeatureExtractor.from_pretrained(MODEL_NAME)
model = AutoModelForAudioClassification.from_pretrained(MODEL_NAME)
model = model.to(device)
model.eval()
logger.info(f"Model loaded on {device}. Labels: {model.config.id2label}")

# ─── FastAPI ──────────────────────────────────────────────────────────────────

app = FastAPI(title="VoiceGuard", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# ─── Audio Utilities ─────────────────────────────────────────────────────────

def convert_audio(audio_bytes: bytes) -> Optional[np.ndarray]:
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
        f.write(audio_bytes)
        in_path = f.name
    out_path = in_path.replace(".webm", ".wav")
    try:
        r = subprocess.run(
            [FFMPEG, "-y", "-i", in_path, "-ar", "16000", "-ac", "1", "-f", "wav", out_path],
            capture_output=True, timeout=30,
        )
        if r.returncode != 0:
            logger.error("FFmpeg error: %s", r.stderr.decode(errors="replace"))
            return None
        audio, _ = librosa.load(out_path, sr=16000, mono=True)
        return audio
    except Exception as e:
        logger.error("Audio conversion: %s", e)
        return None
    finally:
        Path(in_path).unlink(missing_ok=True)
        Path(out_path).unlink(missing_ok=True)




def run_inference(audio: np.ndarray) -> Dict[str, Any]:
    inputs = feature_extractor(audio, sampling_rate=16000, return_tensors="pt", padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=-1)[0]

    id2label = model.config.id2label
    scores = {id2label[i].upper(): float(probs[i]) for i in range(len(probs))}

    fake_score = scores.get("FAKE", scores.get("SPOOF", 0.0))
    real_score = scores.get("REAL", scores.get("BONAFIDE", 1.0 - fake_score))

    return {
        "fake_score": round(fake_score * 100, 1),
        "real_score": round(real_score * 100, 1),
        "verdict": "FAKE" if fake_score > real_score else "REAL",
    }


# ─── Session ─────────────────────────────────────────────────────────────────

class Session:
    FAKE_STREAK_THRESHOLD = 2
    CONFIDENCE_THRESHOLD = 0.80

    def __init__(self):
        self.chunk_count = 0
        self.fake_streak = 0
        self.real_count = 0
        self.fake_count = 0
        self.terminated = False


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index():
    return (static_dir / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME, "device": str(device), "ffmpeg": FFMPEG}


@app.post("/analyze")
async def analyze_file(file: UploadFile = File(...)):
    data = await file.read()
    audio = convert_audio(data)
    if audio is None:
        raise HTTPException(400, "Could not decode audio. Make sure FFmpeg is installed.")

    model_result = run_inference(audio)
    confidence = round(max(model_result["fake_score"], model_result["real_score"]), 1)

    return {
        "verdict": model_result["verdict"],
        "confidence": confidence,
        "fake_score": model_result["fake_score"],
        "real_score": model_result["real_score"],
    }


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    session = Session()
    logger.info("WS connected")
    try:
        while True:
            raw = await websocket.receive_text()
            payload = json.loads(raw)

            if payload.get("type") == "reset":
                session = Session()
                await websocket.send_json({"type": "reset_ack"})
                continue

            chunk_idx = payload.get("idx", 0)
            audio_bytes = base64.b64decode(payload["audio"])

            try:
                audio = convert_audio(audio_bytes)
                if audio is None:
                    await websocket.send_json({"error": "Audio conversion failed", "chunk_idx": chunk_idx})
                    continue

                model_result = run_inference(audio)
                verdict = model_result["verdict"]
                confidence = round(max(model_result["fake_score"], model_result["real_score"]), 1)

                session.chunk_count += 1
                if verdict == "FAKE":
                    session.fake_count += 1
                    if model_result["fake_score"] >= session.CONFIDENCE_THRESHOLD * 100:
                        session.fake_streak += 1
                    else:
                        session.fake_streak = max(0, session.fake_streak - 1)
                else:
                    session.real_count += 1
                    session.fake_streak = 0

                terminate = (
                    session.fake_streak >= session.FAKE_STREAK_THRESHOLD
                    and not session.terminated
                )
                if terminate:
                    session.terminated = True

                await websocket.send_json({
                    "chunk_idx": chunk_idx,
                    "verdict": verdict,
                    "confidence": confidence,
                    "all_scores": {
                        "REAL": model_result["real_score"],
                        "FAKE": model_result["fake_score"],
                    },
                    "fake_streak": session.fake_streak,
                    "cut_call": terminate,
                })

                if terminate:
                    await asyncio.sleep(0.3)
                    break

            except Exception as e:
                import traceback; traceback.print_exc()
                await websocket.send_json({"error": str(e), "chunk_idx": chunk_idx})

    except WebSocketDisconnect:
        logger.info("WS disconnected")
    except Exception as e:
        logger.error("WS error: %s", e)
