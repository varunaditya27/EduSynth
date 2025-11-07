from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .routers import slides
from .core.config import settings

from pydantic import BaseModel
import uuid
from pathlib import Path
from .schema import SlidesPayload
import json

from .gemini_generator import generate_slides  # ✅ Use your generator
from .tts_utils import synthesize_audio
from .video_sync import assemble_video_from_slides

app = FastAPI(title="EduSynth Slide Deck Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(slides.router, prefix="/v1/slides", tags=["slides"])

OUTDIR = Path(__file__).resolve().parent.parent / "output"

class GenerateRequest(BaseModel):
    topic: str
    audience: str
    length: str
    theme: str = "Minimalist"

@app.post("/generate")
def generate(req: GenerateRequest):
    task_id = str(uuid.uuid4())
    try:
        minutes = int(req.length.replace("min", "").strip())
        _, slide_list = generate_slides(req.topic, req.audience, minutes, req.theme)
        slides_payload = {"slides": slide_list}
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
    slides_file = OUTDIR / "slides" / f"{task_id}.json"
    if not slides_file.exists():
        raise HTTPException(status_code=404, detail="slides JSON not found for task_id")

    slides_payload = json.loads(slides_file.read_text(encoding="utf-8"))
    slides = slides_payload.get("slides", [])

    task_dir = OUTDIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    assembled_slides = []
    for s in slides:
        idx = s["index"]
        suggested_duration = float(s.get("duration", 5.0))
        audio_path, actual_duration = synthesize_audio(task_id, idx, s["narration"])
        assembled_slides.append({
            "index": idx,
            "title": s.get("title"),
            "points": s.get("points"),
            "audio_path": audio_path,
            "audio_duration": actual_duration
        })

    video_path = assemble_video_from_slides(task_id, assembled_slides, theme=req.theme)

    timing = [{"slide": s["index"], "audio_duration": s["audio_duration"], "display_duration": s["audio_duration"]} for s in assembled_slides]
    (OUTDIR / task_id / "timing.json").write_text(json.dumps(timing, indent=2), encoding="utf-8")

    return {
        "task_id": task_id,
        "status": "done",
        "video_path": video_path,
        "timing": timing
    }
