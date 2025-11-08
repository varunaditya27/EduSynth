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
from .routers import slides, recommendations, chatbot, mindmap, auth, animations, lectures
from .gemini_generator import generate_slides
from .tts_utils import synthesize_audio
from .video_sync import assemble_video_from_slides
from .db import get_client
from prisma import Prisma
from prisma.enums import VideoStatus, VisualTheme
from datetime import datetime
# merge_utils no longer needed - video already has audio from MoviePy

# --- Setup ---
app = FastAPI(title="EduSynth Backend API")

# Add routers (keep your friend's routes)
app.include_router(auth.router, prefix="/v1/auth", tags=["authentication"])
app.include_router(lectures.router, prefix="/api/lectures", tags=["lectures"])
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

    # Upload with public-read ACL so videos are publicly accessible
    s3.upload_file(
        str(local_path), 
        bucket, 
        s3_key,
        ExtraArgs={'ACL': 'public-read', 'ContentType': 'video/mp4'}
    )

    # Construct the public R2 URL
    # Format: https://<bucket-name>.<account-id>.r2.cloudflarestorage.com/<s3-key>
    # Or if you have a custom domain: https://your-domain.com/<s3-key>
    # For now, construct from endpoint
    r2_public_url = getattr(settings, "CLOUDFLARE_R2_PUBLIC_URL", None)
    if r2_public_url:
        return f"{r2_public_url.rstrip('/')}/{s3_key}"
    
    # Fallback: construct from endpoint
    # Remove the API endpoint and construct public URL
    # Cloudflare R2 endpoint format: https://<account-id>.r2.cloudflarestorage.com
    # Public URL format: https://pub-<hash>.<region>.r2.dev/<key>
    # Or: https://<bucket>.r2.cloudflarestorage.com/<key>
    return f"{endpoint.rstrip('/')}/{s3_key}"


@app.get("/status/{task_id}")
def get_status(task_id: str):
    """
    Get the status of video generation for a given task_id.
    Returns status, progress, and URLs when complete.
    """
    try:
        # Check if slides JSON exists
        slides_file = OUTDIR / "slides" / f"{task_id}.json"
        if not slides_file.exists():
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        # Load slides data to get topic
        slides_payload = json.loads(slides_file.read_text(encoding="utf-8"))
        slides = slides_payload.get("slides", [])
        topic = slides[0].get("title", "Lecture") if slides else "Lecture"
        
        # Check if video exists in final directory
        final_dir = OUTDIR / task_id / "final"
        final_video = final_dir / f"{task_id}_merged.mp4"
        
        if final_video.exists():
            # Video is complete - construct public R2 URL
            try:
                # Read meta.json to get the actual uploaded URL
                meta_file = OUTDIR / task_id / "meta.json"
                if meta_file.exists():
                    meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
                    video_url = meta_data.get("final_cloud_url")
                    if video_url:
                        return {
                            "task_id": task_id,
                            "status": "completed",
                            "progress": 100,
                            "topic": topic,
                            "videoUrl": video_url,
                            "message": "Video generation complete"
                        }
                
                # Fallback: construct public URL from settings
                r2_public_url = getattr(settings, "CLOUDFLARE_R2_PUBLIC_URL", None)
                if r2_public_url:
                    # Use the same s3_key format as in assemble_background_task
                    s3_key = f"edusynth/{task_id}/{task_id}_merged.mp4"
                    video_url = f"{r2_public_url.rstrip('/')}/{s3_key}"
                else:
                    # Last resort: use endpoint (but this won't be publicly accessible)
                    endpoint = settings.CLOUDFLARE_S3_ENDPOINT
                    s3_key = f"edusynth/{task_id}/{task_id}_merged.mp4"
                    video_url = f"{endpoint.rstrip('/')}/{s3_key}"
                
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "progress": 100,
                    "topic": topic,
                    "videoUrl": video_url,
                    "message": "Video generation complete"
                }
            except Exception as e:
                # If R2 URL construction fails, return local file
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "progress": 100,
                    "topic": topic,
                    "videoUrl": f"/output/{task_id}/final/{task_id}_merged.mp4",
                    "message": "Video generation complete (local)"
                }
        
        # Check if video is being assembled (exists in video directory but not final)
        video_dir = OUTDIR / task_id / "video"
        video_file = video_dir / f"{task_id}.mp4"
        
        if video_file.exists():
            return {
                "task_id": task_id,
                "status": "processing",
                "progress": 90,
                "topic": topic,
                "message": "Finalizing video..."
            }
        
        # Check if audio files exist (TTS stage)
        audio_dir = OUTDIR / task_id / "audio"
        if audio_dir.exists() and list(audio_dir.glob("*.mp3")):
            audio_count = len(list(audio_dir.glob("*.mp3")))
            expected_count = len(slides)
            progress = 40 + (audio_count / expected_count * 40) if expected_count > 0 else 40
            
            return {
                "task_id": task_id,
                "status": "processing",
                "progress": int(progress),
                "topic": topic,
                "message": f"Generating voiceover ({audio_count}/{expected_count})..."
            }
        
        # Task exists but processing hasn't started much
        return {
            "task_id": task_id,
            "status": "processing",
            "progress": 20,
            "topic": topic,
            "message": "Preparing slides..."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@app.post("/generate")
async def generate(req: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Generates slides via Gemini, saves JSON, and triggers background assembly.
    """
    task_id = str(uuid.uuid4())
    minutes = _parse_minutes(req.length)

    try:
        theme = req.theme or "Minimalist"
        _, slide_list = generate_slides(req.topic, req.audience, minutes, theme)
        slides_payload = {"slides": slide_list}
        saved_path = _save_slides_json(task_id, slides_payload)
        
        # Parse theme to enum
        theme_upper = theme.upper()
        visual_theme = VisualTheme.MINIMALIST  # default
        if hasattr(VisualTheme, theme_upper):
            visual_theme = getattr(VisualTheme, theme_upper)
        
        # Create lecture record in database
        db = await get_client()
        lecture_data = {
            "id": task_id,
            "topic": req.topic,
            "targetAudience": req.audience,
            "desiredLength": minutes,
            "visualTheme": visual_theme,
            "videoStatus": VideoStatus.GENERATING_CONTENT,
            "processingStartedAt": datetime.utcnow(),
            "hasInteractive": False
        }
        # Don't include userId if it's None - let the database handle the default
        await db.lecture.create(data=lecture_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")

    # Trigger background video assembly automatically
    background_tasks.add_task(assemble_background_task_wrapper, task_id, theme)

    return {
        "task_id": task_id,
        "status": "processing",
        "message": "Slides generated successfully. Video generation has started in background.",
    }


def assemble_background_task_wrapper(task_id: str, theme: str):
    """Wrapper to run async task in background."""
    import asyncio
    try:
        # Create new event loop for this background thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(assemble_background_task(task_id, theme))
        loop.close()
    except Exception as e:
        print(f"[❌ Background task wrapper error]: {e}")


async def assemble_background_task(task_id: str, theme: str):
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
        
        # Update lecture record in database
        db = await get_client()
        await db.lecture.update(
            where={"id": task_id},
            data={
                "videoUrl": cloud_url,
                "videoStatus": VideoStatus.COMPLETED,
                "processingCompletedAt": datetime.utcnow()
            }
        )
        print(f"[✅ DATABASE] Lecture record updated: {task_id}")

    except Exception as e:
        print(f"[❌ ERROR in background task {task_id}]: {e}")
        # Update lecture status to failed
        try:
            db = await get_client()
            await db.lecture.update(
                where={"id": task_id},
                data={
                    "videoStatus": VideoStatus.FAILED,
                    "errorMessage": str(e),
                    "processingCompletedAt": datetime.utcnow()
                }
            )
        except Exception as db_error:
            print(f"[❌ DATABASE ERROR]: Could not update failed status: {db_error}")
@app.post("/assemble_background_task/{task_id}")
async def assemble_background_route(task_id: str):
    """Manual endpoint for testing background assembly."""
    try:
        theme = "Minimalist"  # Default theme if not stored
        await assemble_background_task(task_id, theme)
        return {"status": "ok", "task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    