from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import slides, recommendations
from .core.config import settings

app = FastAPI(title="EduSynth Slide Deck Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(slides.router, prefix="/v1/slides", tags=["slides"])
app.include_router(recommendations.router, prefix="/v1/recommendations", tags=["recommendations"])
# backend/app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
from pathlib import Path
from .gemini_utils import generate_mock_slides
from .schema import SlidesPayload
import json

# new imports
from .tts_utils import synthesize_audio

from .video_sync import assemble_video_from_slides

app = FastAPI()
OUTDIR = Path(__file__).resolve().parent.parent / "output"

class GenerateRequest(BaseModel):
    prompt: str
    topic: str
    audience: str
    length: str
    theme: str = "Minimalist"

@app.post("/generate")
def generate(req: GenerateRequest):
    task_id = str(uuid.uuid4())
    try:
        slides_payload = generate_mock_slides(task_id, req.topic, req.audience, req.length, req.theme)
        SlidesPayload.parse_obj(slides_payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"generation failed: {e}")

    return {
        "task_id": task_id,
        "status": "slides_generated",
        "slides": slides_payload["slides"]
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/assemble/{task_id}")
def assemble(task_id: str):
    """
    Reads output/slides/<task_id>.json
    Synthesizes audio for each slide (silent stub) and assembles final mp4.
    Returns the path to the video and timing info.
    """
    slides_file = OUTDIR / "slides" / f"{task_id}.json"
    if not slides_file.exists():
        raise HTTPException(status_code=404, detail="slides JSON not found for task_id")

    slides_payload = json.loads(slides_file.read_text(encoding="utf-8"))
    slides = slides_payload.get("slides", [])

    # Create output folder for this task
    task_dir = OUTDIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    assembled_slides = []
    for s in slides:
        idx = s["index"]
        suggested_duration = float(s.get("duration", 5.0))
        # Synthesize audio (silent stub)
        audio_path, actual_duration = synthesize_audio(task_id, idx, s["narration"])
        assembled_slides.append({
            "index": idx,
            "title": s.get("title"),
            "points": s.get("points"),
            "audio_path": audio_path,
            "audio_duration": actual_duration
        })

    # Assemble video
    video_path = assemble_video_from_slides(task_id, assembled_slides, theme="Minimalist")

    # Save timing info
    timing = [{"slide": s["index"], "audio_duration": s["audio_duration"], "display_duration": s["audio_duration"]} for s in assembled_slides]
    (OUTDIR / task_id / "timing.json").write_text(json.dumps(timing, indent=2), encoding="utf-8")

    return {
        "task_id": task_id,
        "status": "done",
        "video_path": video_path,
        "timing": timing
    }
