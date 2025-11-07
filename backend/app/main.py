# backend/app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
from pathlib import Path
from .gemini_utils import generate_mock_slides
from .schema import SlidesPayload

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
        # For now we call the mock generator. Replace with real Gemini call later.
        slides_payload = generate_mock_slides(task_id, req.topic, req.audience, req.length, req.theme)
        # Validate using pydantic schema
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
