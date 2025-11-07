from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, BackgroundTasks
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
from .routers import slides, recommendations, chatbot, mindmap, auth, animations
from .gemini_generator import generate_slides
from .tts_utils import synthesize_audio
from .video_sync import assemble_video_from_slides
# merge_utils no longer needed - video already has audio from MoviePy

# --- Setup ---
app = FastAPI(title="EduSynth Backend API")

# Add routers (keep your friend's routes)
app.include_router(auth.router, prefix="/v1/auth", tags=["authentication"])
app.include_router(slides.router, prefix="/v1/slides", tags=["slides"])
app.include_router(recommendations.router, prefix="/v1/recommendations", tags=["recommendations"])
app.include_router(chatbot.router, prefix="/v1/chatbot", tags=["chatbot"])
app.include_router(mindmap.router, prefix="/v1/mindmap", tags=["mindmap"])
app.include_router(animations.router, prefix="/v1/animations", tags=["animations"])

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
    bucket = settings.CLOUDFLARE_S3_BUCKET_NAME
    access_key = settings.CLOUDFLARE_S3_ACCESS_KEY_ID
    secret_key = settings.CLOUDFLARE_S3_SECRET_ACCESS_KEY

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
def generate(req: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Generates slides via Gemini, saves JSON, and triggers background assembly.
    """
    task_id = str(uuid.uuid4())
    minutes = _parse_minutes(req.length)

    try:
        _, slide_list = generate_slides(req.topic, req.audience, minutes, req.theme)
        slides_payload = {"slides": slide_list}
        saved_path = _save_slides_json(task_id, slides_payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini generation failed: {e}")

    # Trigger background video assembly automatically
    background_tasks.add_task(assemble_background_task, task_id, req.theme)

    return {
        "task_id": task_id,
        "status": "processing",
        "message": "Slides generated successfully. Video generation has started in background.",
    }


def assemble_background_task(task_id: str, theme: str):
    """
    Internal background worker — runs assemble() logic automatically.
    """
    try:
        slides_file = OUTDIR / "slides" / f"{task_id}.json"
        slides_payload = json.loads(slides_file.read_text(encoding="utf-8"))
        slides = slides_payload.get("slides", [])
        task_dir = OUTDIR / task_id
        for sub in ["audio", "slides_images", "final"]:
            (task_dir / sub).mkdir(parents=True, exist_ok=True)

        assembled_slides = []
        for s in slides:
            idx = int(s.get("index", 0))
            narration = s.get("narration", "")
            audio_path, actual_duration = synthesize_audio(task_id, idx, narration)
            assembled_slides.append({
                "index": idx,
                "title": s.get("title"),
                "points": s.get("points"),
                "narration": narration,
                "audio_path": audio_path,
                "audio_duration": actual_duration,
                "display_duration": actual_duration
            })

        video_path = assemble_video_from_slides(task_id, assembled_slides, theme=theme)
        
        # Video already has audio embedded - no merge needed!
        # Copy to final directory for upload
        final_dir = OUTDIR / task_id / "final"
        final_dir.mkdir(parents=True, exist_ok=True)
        final_path = final_dir / f"{task_id}_merged.mp4"
        
        # Copy the video with audio to final location
        import shutil
        shutil.copy2(video_path, final_path)
        s3_key = f"edusynth/{task_id}/{final_path.name}"
        cloud_url = _upload_file_to_r2(final_path, s3_key)

        print(f"[✅ COMPLETED] Lecture ready: {cloud_url}")

        # Save metadata
        (OUTDIR / task_id / "meta.json").write_text(
            json.dumps({"final_cloud_url": cloud_url}, indent=2),
            encoding="utf-8"
        )

    except Exception as e:
        print(f"[❌ ERROR in background task {task_id}]: {e}")
@app.post("/assemble_background_task/{task_id}")
def assemble_background_route(task_id: str):
    """Manual endpoint for testing background assembly."""
    try:
        theme = "Minimalist"  # Default theme if not stored
        assemble_background_task(task_id, theme)
        return {"status": "ok", "task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    