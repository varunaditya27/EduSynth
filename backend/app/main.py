from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from .gemini_generator import generate_slides

# --- Load .env at app startup ---
# Looks for .env in the repo root
env_path = find_dotenv(".env", usecwd=True)
load_dotenv(env_path)

# Temporary debug print (will print once on startup)
if os.getenv("GEMINI_API_KEY"):
    print("✅ GEMINI_API_KEY loaded successfully.")
else:
    print("⚠️ GEMINI_API_KEY NOT FOUND. Check .env placement and spelling.")


app = FastAPI()


class GenerateRequest(BaseModel):
    topic: str
    audience: str
    minutes: int
    theme: str


@app.post("/generate")
def generate(req: GenerateRequest):
    try:
        task_id, slides = generate_slides(req.topic, req.audience, req.minutes, req.theme)
        return {
            "task_id": task_id,
            "slides": slides,
            "status": "slides_generated"
        }
    except Exception as e:
        # Print error to terminal for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
