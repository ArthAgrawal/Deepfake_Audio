import numpy as np
import json
import base64
import tempfile
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

import torch
from transformers import AutoModelForAudioClassification, AutoFeatureExtractor
import librosa

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# Configuration
FFMPEG = os.getenv("FFMPEG_PATH", "ffmpeg")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Verify ffmpeg exists
try:
    subprocess.run([FFMPEG, "-version"], capture_output=True, check=True)
    print(f"✓ FFmpeg found at: {FFMPEG}")
except (FileNotFoundError, subprocess.CalledProcessError) as e:
    print(f"⚠ Warning: FFmpeg not found at '{FFMPEG}'")
    print(f"  Please set FFMPEG_PATH in .env file or install ffmpeg")
    print(f"  Audio processing will fail without ffmpeg")

# Load HuggingFace model
MODEL_NAME = "Gustking/wav2vec2-large-xlsr-deepfake-audio-classification"
print("Loading model...")
feature_extractor = AutoFeatureExtractor.from_pretrained(MODEL_NAME)
model = AutoModelForAudioClassification.from_pretrained(MODEL_NAME)
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
model.eval()
print(f"✓ Model loaded on {device}")

app = FastAPI(title="VoiceGuard - Deepfake Audio Detector")

# Enable CORS for public access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

def preprocess_audio(audio_bytes):
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp_in:
        tmp_in.write(audio_bytes)
        tmp_in_path = tmp_in.name

    tmp_out_path = tmp_in_path.replace(".webm", ".wav")

    subprocess.run([
        FFMPEG, "-y",
        "-i", tmp_in_path,
        "-ar", "16000",   # wav2vec2 expects 16kHz
        "-ac", "1",
        tmp_out_path
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    y, sr = librosa.load(tmp_out_path, sr=16000, mono=True)

    os.remove(tmp_in_path)
    os.remove(tmp_out_path)

    return y, sr

def run_inference(y, sr):
    inputs = feature_extractor(
        y,
        sampling_rate=sr,
        return_tensors="pt",
        padding=True
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.nn.functional.softmax(logits, dim=-1)

    # Get label mapping from model config
    id2label = model.config.id2label
    prob_list = probs[0].tolist()

    # Find real and fake probs
    scores = {id2label[i].upper(): round(prob_list[i] * 100, 2) for i in range(len(prob_list))}

    # Determine verdict
    fake_score = scores.get("FAKE", scores.get("SPOOF", 0))
    real_score = scores.get("REAL", scores.get("BONAFIDE", 0))

    verdict = "FAKE" if fake_score > real_score else "REAL"
    confidence = round(max(fake_score, real_score), 2)

    return verdict, confidence, scores

@app.get("/", response_class=HTMLResponse)
def index():
    with open("static/index.html", encoding="utf-8") as f:
        return f.read()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")
    fake_streak = 0

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            chunk_idx = payload.get("idx", 0)
            audio_bytes = base64.b64decode(payload["audio"])

            try:
                y, sr = preprocess_audio(audio_bytes)
                verdict, confidence, scores = run_inference(y, sr)

                is_fake = verdict == "FAKE"

                if is_fake and confidence > 85:
                    fake_streak += 1
                else:
                    fake_streak = 0

                cut_call = fake_streak >= 2

                await websocket.send_json({
                    "chunk_idx": chunk_idx,
                    "verdict": verdict,
                    "predicted_class": verdict,
                    "confidence": confidence,
                    "all_scores": scores,
                    "cut_call": cut_call,
                    "fake_streak": fake_streak
                })

                if cut_call:
                    fake_streak = 0

            except Exception as e:
                import traceback
                traceback.print_exc()
                await websocket.send_json({"error": str(e)})

    except WebSocketDisconnect:
        print("Client disconnected")