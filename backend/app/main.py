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

# Local imports (use your existing modules)
from .core.config import settings
from .gemini_generator import generate_slides
from .tts_utils import synthesize_audio
from .video_sync import assemble_video_from_slides
from .merge_utils import merge_audio_video

# --- Setup ---
app = FastAPI(title="EduSynth Backend API")
OUTDIR = Path(__file__).resolve().parent.parent / "output"  # backend/output
OUTDIR.mkdir(parents=True, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------- MODELS -----------
class GenerateRequest(BaseModel):
    topic: str
    audience: str
    length: str  # e.g. "10" or "10 min" — we'll parse int
    theme: Optional[str] = "Minimalist"
# -------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


def _parse_minutes(length: str) -> int:
    """Try to parse minute value (int). Accept '10', '10 min', '10minutes'."""
    if isinstance(length, int):
        return int(length)
    if not length:
        return 5
    s = str(length).lower().replace("minutes", "").replace("minute", "").replace("min", "").strip()
    try:
        return max(1, int(float(s)))
    except Exception:
        # fallback default
        return 5


def _save_slides_json(task_id: str, slides_payload: dict):
    slides_dir = OUTDIR / "slides"
    slides_dir.mkdir(parents=True, exist_ok=True)
    path = slides_dir / f"{task_id}.json"
    path.write_text(json.dumps(slides_payload, indent=2), encoding="utf-8")
    return path


def _upload_file_to_r2(local_path: Path, s3_key: str) -> str:
    """
    Upload a file to Cloudflare R2 (S3-compatible) using boto3.
    Returns a public URL constructed from DIRECT_URL if provided, else build from endpoint.
    """
    # Read credentials from settings (config aliases handled by your config)
    endpoint = settings.CLOUDFLARE_S3_ENDPOINT
    bucket = settings.CLOUDFLARE_S3_BUCKET
    access_key = getattr(settings, "CLOUDFLARE_S3_ACCESS_KEY", None)
    secret_key = getattr(settings, "CLOUDFLARE_S3_SECRET_KEY", None)
    # Fallback alias names if present
    if getattr(settings, "CLOUDFLARE_S3_ACCESS_KEY_ID", None):
        access_key = getattr(settings, "CLOUDFLARE_S3_ACCESS_KEY_ID")
    if getattr(settings, "CLOUDFLARE_S3_SECRET_ACCESS_KEY", None):
        secret_key = getattr(settings, "CLOUDFLARE_S3_SECRET_ACCESS_KEY")

    if not all([endpoint, bucket, access_key, secret_key]):
        raise RuntimeError("Missing Cloudflare R2 configuration in settings. Check CLOUDFLARE_* env vars.")

    # Create boto3 s3 client configured for R2
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=BotoConfig(signature_version="s3v4"),
    )

    # Upload
    s3.upload_file(str(local_path), bucket, s3_key)

    # Construct public URL:
    # Prefer DIRECT_URL (if provided) which should be the public domain configured to serve objects.
    direct = getattr(settings, "DIRECT_URL", None)
    if direct:
        return f"{direct.rstrip('/')}/{s3_key}"
    # Fallback to endpoint-based URL (may or may not be public depending on config)
    ep = endpoint.rstrip("/")
    return f"{ep}/{bucket}/{s3_key}"


@app.post("/generate")
def generate(req: GenerateRequest):
    """
    Creates slide JSON structure from Gemini (via gemini_generator.generate_slides).
    Saves cleaned slides JSON to backend/output/slides/<task_id>.json so assemble() can consume it.
    Returns the task_id and slides to the frontend.
    """
    task_id = str(uuid.uuid4())
    minutes = _parse_minutes(req.length)

    try:
        # generate_slides returns (task_id_from_generator, slides_list)
        gen_task_id, slide_list = generate_slides(req.topic, req.audience, minutes, req.theme)
        # NOTE: gemini_generator already creates its own timestamp task_id.
        # We will use our own UUID for the pipeline but keep the generated slides content.
        slides_payload = {"slides": slide_list}
        # validate with your schema if you want — import and call SlidesPayload.parse_obj(...) as needed
        # Save slides JSON for assemble
        saved_path = _save_slides_json(task_id, slides_payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")

    return {
        "task_id": task_id,
        "status": "slides_generated",
        "slides_path": str(saved_path),
        "slides": slides_payload["slides"],
    }


@app.post("/assemble/{task_id}")
def assemble(task_id: str):
    """
    Reads saved slides JSON → Synthesizes audio → Builds video slides → Merges final MP4 → Uploads to R2.
    Returns the cloud URL to the final MP4.
    """
    slides_file = OUTDIR / "slides" / f"{task_id}.json"
    if not slides_file.exists():
        raise HTTPException(status_code=404, detail="slides JSON not found for task_id")

    slides_payload = json.loads(slides_file.read_text(encoding="utf-8"))
    slides = slides_payload.get("slides", [])
    if not slides:
        raise HTTPException(status_code=400, detail="No slides found in slides JSON")

    # Create task output folder
    task_dir = OUTDIR / task_id
    audio_dir = task_dir / "audio"
    images_dir = task_dir / "slides_images"
    final_dir = task_dir / "final"
    for d in (task_dir, audio_dir, images_dir, final_dir):
        d.mkdir(parents=True, exist_ok=True)

    assembled_slides = []
    # Synthesize TTS for each slide (synthesize_audio should return (path, duration_seconds))
    for s in slides:
        idx = int(s.get("index", 0))
        narration_text = s.get("narration", "")
        target_duration = float(s.get("duration", 8.0))

        try:
            audio_path, actual_duration = synthesize_audio(task_id, idx, narration_text)
        except Exception as e:
            # If TTS fails for a slide, bubble up a readable error
            raise HTTPException(status_code=500, detail=f"TTS failed for slide {idx}: {e}")

        # Auto-sync logic: trust TTS duration (actual_duration). If model durations differ a lot, we logged earlier.
        display_duration = float(actual_duration)
        assembled_slides.append({
            "index": idx,
            "title": s.get("title"),
            "points": s.get("points"),
            "narration": narration_text,
            "audio_path": audio_path,
            "audio_duration": float(actual_duration),
            "display_duration": display_duration
        })

    # Assemble silent video (images + subtitles) using your existing function
    try:
        video_path = assemble_video_from_slides(task_id, assembled_slides, theme="Minimalist")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video assembly failed: {e}")

    # Save timing info for debugging / client
    timing = [
        {
            "slide": s["index"],
            "audio_duration": s["audio_duration"],
            "display_duration": s["display_duration"]
        } for s in assembled_slides
    ]
    (task_dir / "timing.json").write_text(json.dumps(timing, indent=2), encoding="utf-8")

    # Merge audio + video into final MP4
    try:
        final_path = merge_audio_video(task_id)
    except Exception as e:
        # If merge fails, we still can try uploading the silent video
        try:
            final_path = Path(video_path)
        except Exception:
            raise HTTPException(status_code=500, detail=f"FFmpeg merge failed and no fallback video available: {e}")

    if not final_path or not Path(final_path).exists():
        raise HTTPException(status_code=500, detail="Final video file not found after merge.")

    final_path = Path(final_path)

    # Upload final to Cloudflare R2 and return public URL
    try:
        # Use a deterministic key that contains task_id so files are easy to find
        s3_key = f"edusynth/{task_id}/{final_path.name}"
        cloud_url = _upload_file_to_r2(final_path, s3_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload to R2 failed: {e}")

    return {
        "task_id": task_id,
        "status": "done",
        "final_local_path": str(final_path),
        "final_cloud_url": cloud_url,
        "timing": timing
    }
