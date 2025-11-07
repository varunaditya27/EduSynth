from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .routers import slides, recommendations, chatbot
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
app.include_router(recommendations.router, prefix="/v1/recommendations", tags=["recommendations"])
app.include_router(chatbot.router, prefix="/v1/chatbot", tags=["chatbot"])
# backend/app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
from pathlib import Path
import json

# Local imports
from .tts_utils import synthesize_audio
from .video_sync import assemble_video_from_slides
from .gemini_utils import generate_mock_slides   # Person A will replace this with real Gemini integration
from .schema import SlidesPayload
from .merge_utils import merge_audio_video   # 👈 new import for post-processing merge

# Initialize FastAPI app
app = FastAPI(title="EduSynth Backend API")
OUTDIR = Path(__file__).resolve().parent.parent / "output"


# ----------- MODELS -----------
class GenerateRequest(BaseModel):
    topic: str
    audience: str
    length: str
    theme: str = "Minimalist"
# -------------------------------


# ----------- ROUTES ------------

@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/generate")
def generate(req: GenerateRequest):
    """
    Creates slide JSON structure from Gemini or mock generator.
    """
    task_id = str(uuid.uuid4())
    try:
        minutes = int(req.length.replace("min", "").strip())
        _, slide_list = generate_slides(req.topic, req.audience, minutes, req.theme)
        slides_payload = {"slides": slide_list}
        SlidesPayload.parse_obj(slides_payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")

    return {
        "task_id": task_id,
        "status": "slides_generated",
        "slides": slides_payload["slides"]
    }


@app.post("/assemble/{task_id}")
def assemble(task_id: str):
    """
    Reads slides JSON → Synthesizes audio → Builds video slides → Merges final MP4.
    """
    slides_file = OUTDIR / "slides" / f"{task_id}.json"
    if not slides_file.exists():
        raise HTTPException(status_code=404, detail="slides JSON not found for task_id")

    slides_payload = json.loads(slides_file.read_text(encoding="utf-8"))
    slides = slides_payload.get("slides", [])

    # Create output folder
    task_dir = OUTDIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    assembled_slides = []
    for s in slides:
        idx = s["index"]
        narration_text = s.get("narration", "")
        target_duration = float(s.get("duration", 5.0))

        # Generate ElevenLabs audio
        audio_path, actual_duration = synthesize_audio(task_id, idx, narration_text)

        # --- Auto-sync logic ---
        display_duration = actual_duration
        if abs(actual_duration - target_duration) > 1.5:
            print(f"[SYNC] Slide {idx}: Adjusting {target_duration}s → {actual_duration}s")
        # -----------------------

        suggested_duration = float(s.get("duration", 5.0))
        audio_path, actual_duration = synthesize_audio(task_id, idx, s["narration"])
        assembled_slides.append({
            "index": idx,
            "title": s.get("title"),
            "points": s.get("points"),
            "narration": narration_text,
            "audio_path": audio_path,
            "audio_duration": actual_duration,
            "display_duration": display_duration
        })

    # Step 1: Assemble silent video with subtitles + fade transitions
    video_path = assemble_video_from_slides(task_id, assembled_slides, theme="Minimalist")

    # Step 2: Save timing info
    timing = [
        {
            "slide": s["index"],
            "audio_duration": s["audio_duration"],
            "display_duration": s["display_duration"]
        }
        for s in assembled_slides
    ]
    (OUTDIR / task_id / "timing.json").write_text(
        json.dumps(timing, indent=2), encoding="utf-8"
    )

    # Step 3: Merge audio + video into one final MP4 using ffmpeg
    try:
        final_path = merge_audio_video(task_id)
    except Exception as e:
        print(f"[ERROR] FFmpeg merge failed: {e}")
        final_path = video_path  # fallback

    # Step 4: Return response
    return {
        "task_id": task_id,
        "status": "done",
        "video_path": video_path,
        "final_video_path": final_path,
        "timing": timing
    }

# -------------------------------
