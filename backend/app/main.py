from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import uuid
import json
import os
import boto3
from botocore.client import Config as BotoConfig
from typing import Optional

# Local imports
from .core.config import settings
from .routers import slides, recommendations, chatbot, mindmap
from .gemini_generator import generate_slides
from .tts_utils import synthesize_audio
from .video_sync import assemble_video_from_slides
from .merge_utils import merge_audio_video

# --- Setup ---
app = FastAPI(title="EduSynth Backend API")

# Add routers (keep your friend’s routes)
app.include_router(slides.router, prefix="/v1/slides", tags=["slides"])
app.include_router(recommendations.router, prefix="/v1/recommendations", tags=["recommendations"])
app.include_router(chatbot.router, prefix="/v1/chatbot", tags=["chatbot"])
app.include_router(mindmap.router, prefix="/v1/mindmap", tags=["mindmap"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTDIR = Path(__file__).resolve().parent.parent / "output"
OUTDIR.mkdir(parents=True, exist_ok=True)

# ----------- MODELS -----------
class GenerateRequest(BaseModel):
    topic: str
    audience: str
    length: str  # e.g. "10" or "10 min"
    theme: Optional[str] = "Minimalist"
# -------------------------------


@app.get("/health")
def health():
    return {"status": "ok"}


def _parse_minutes(length: str) -> int:
    """Convert string like '10 min' → int."""
    if isinstance(length, int):
        return length
    if not length:
        return 5
    s = str(length).lower().replace("minutes", "").replace("minute", "").replace("min", "").strip()
    try:
        return max(1, int(float(s)))
    except Exception:
        return 5


def _save_slides_json(task_id: str, slides_payload: dict):
    slides_dir = OUTDIR / "slides"
    slides_dir.mkdir(parents=True, exist_ok=True)
    path = slides_dir / f"{task_id}.json"
    path.write_text(json.dumps(slides_payload, indent=2), encoding="utf-8")
    return path


def _upload_file_to_r2(local_path: Path, s3_key: str) -> str:
    """Upload final video to Cloudflare R2 (S3-compatible)."""
    endpoint = settings.CLOUDFLARE_S3_ENDPOINT
    bucket = settings.CLOUDFLARE_S3_BUCKET
    access_key = getattr(settings, "CLOUDFLARE_S3_ACCESS_KEY_ID", None)
    secret_key = getattr(settings, "CLOUDFLARE_S3_SECRET_ACCESS_KEY", None)

    if not all([endpoint, bucket, access_key, secret_key]):
        raise RuntimeError("Missing Cloudflare R2 configuration. Check .env.")

    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=BotoConfig(signature_version="s3v4"),
    )

    s3.upload_file(str(local_path), bucket, s3_key)

    direct = getattr(settings, "DIRECT_URL", None)
    if direct:
        return f"{direct.rstrip('/')}/{s3_key}"
    return f"{endpoint.rstrip('/')}/{bucket}/{s3_key}"


@app.post("/generate")
def generate(req: GenerateRequest):
    """Generate slides from Gemini and save JSON for assembly."""
    task_id = str(uuid.uuid4())
    minutes = _parse_minutes(req.length)

    try:
        _, slide_list = generate_slides(req.topic, req.audience, minutes, req.theme)
        slides_payload = {"slides": slide_list}
        saved_path = _save_slides_json(task_id, slides_payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini generation failed: {e}")

    return {
        "task_id": task_id,
        "status": "slides_generated",
        "slides_path": str(saved_path),
        "slides": slide_list,
    }


@app.post("/assemble/{task_id}")
def assemble(task_id: str):
    """Synthesize audio + video and upload final MP4 to Cloudflare R2."""
    slides_file = OUTDIR / "slides" / f"{task_id}.json"
    if not slides_file.exists():
        raise HTTPException(status_code=404, detail="slides JSON not found for task_id")

    slides_payload = json.loads(slides_file.read_text(encoding="utf-8"))
    slides = slides_payload.get("slides", [])
    if not slides:
        raise HTTPException(status_code=400, detail="Empty slides JSON")

    task_dir = OUTDIR / task_id
    for sub in ["audio", "slides_images", "final"]:
        (task_dir / sub).mkdir(parents=True, exist_ok=True)

    assembled_slides = []
    for s in slides:
        idx = int(s.get("index", 0))
        narration = s.get("narration", "")
        try:
            audio_path, actual_duration = synthesize_audio(task_id, idx, narration)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"TTS failed for slide {idx}: {e}")

        assembled_slides.append({
            "index": idx,
            "title": s.get("title"),
            "points": s.get("points"),
            "narration": narration,
            "audio_path": audio_path,
            "audio_duration": actual_duration,
            "display_duration": actual_duration
        })

    try:
        video_path = assemble_video_from_slides(task_id, assembled_slides, theme="Minimalist")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video assembly failed: {e}")

    timing = [{"slide": s["index"], "audio_duration": s["audio_duration"]} for s in assembled_slides]
    (task_dir / "timing.json").write_text(json.dumps(timing, indent=2), encoding="utf-8")

    try:
        final_path = merge_audio_video(task_id)
    except Exception as e:
        print(f"[WARN] Merge failed: {e}")
        final_path = video_path

    if not Path(final_path).exists():
        raise HTTPException(status_code=500, detail="Final video file missing after merge.")

    try:
        s3_key = f"edusynth/{task_id}/{Path(final_path).name}"
        cloud_url = _upload_file_to_r2(Path(final_path), s3_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload to Cloudflare failed: {e}")

    return {
        "task_id": task_id,
        "status": "done",
        "final_cloud_url": cloud_url,
        "timing": timing
    }
