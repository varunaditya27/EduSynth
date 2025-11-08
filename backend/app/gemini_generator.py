import os, json, re, time
from pathlib import Path
from typing import List, Dict, Tuple
import google.generativeai as genai

# ---------------------------
# Gemini Setup
# ---------------------------
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in environment.")

genai.configure(api_key=API_KEY)
MODEL_NAME = "gemini-2.5-pro"
GENERATION_CONFIG = {"response_mime_type": "application/json", "temperature": 0.5, "top_p": 0.9}

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "ai_generation" / "output" / "raw_gemini"
CLEAN_DIR = ROOT / "ai_generation" / "output" / "slides"
for d in (RAW_DIR, CLEAN_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------
# Core logic
# ---------------------------
def _prompt(topic: str, audience: str, minutes: int, theme: str) -> str:
    return f"""
You are an expert educational content designer and narrator assistant.
Generate a structured educational lecture that matches the target duration and pacing.

Topic: {topic}
Audience: {audience}
Target duration: {minutes} minutes
Visual theme: {theme}

Rules:
- Create 6–10 slides.
- Each slide must include:
  - index
  - title
  - points (2–4 concise bullet points)
  - narration (spoken paragraph, 80–120 words)
  - duration (seconds; estimate narration time at ~130 words per minute)
- Ensure total duration ≈ target duration × 60 seconds (within ±10%).
- Return only valid JSON (no markdown, no commentary).

Example JSON:
{{
  "slides": [
    {{
      "index": 0,
      "title": "Introduction to Photosynthesis",
      "points": ["Plants use sunlight to make food", "Occurs in chloroplasts"],
      "narration": "Photosynthesis is the process by which plants use sunlight to produce energy...",
      "duration": 25.4
    }}
  ]
}}
"""

# ✅ FIXED FUNCTION HERE
def _call_gemini(prompt: str) -> str:
    model = genai.GenerativeModel(MODEL_NAME, generation_config=GENERATION_CONFIG)
    try:
        # Structured input as required in latest Gemini SDK
        response = model.generate_content(
            contents=[{"role": "user", "parts": [{"text": prompt}]}]
        )
        # Safely extract text output
        if hasattr(response, "text") and response.text:
            return response.text.strip()
        elif hasattr(response, "candidates") and response.candidates:
            return response.candidates[0].content.parts[0].text.strip()
        else:
            raise ValueError("No valid text output from Gemini response")
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {e}")

def _extract_json(raw: str) -> str:
    s, e = raw.find("{"), raw.rfind("}")
    if s == -1 or e == -1:
        raise ValueError("No JSON found in Gemini output")
    return raw[s:e+1]

def _word_count(s: str):
    return len(re.findall(r"\w+", s or ""))

def _normalize(slides: List[Dict], minutes: int):
    total = sum(s.get("duration", 0) for s in slides) or 1
    target = minutes * 60
    scale = target / total
    for s in slides:
        s["duration"] = round(s.get("duration", 10) * scale, 2)
    for i, s in enumerate(slides):
        s["index"] = i
    return slides

def generate_slides(topic: str, audience: str, minutes: int, theme: str) -> Tuple[str, List[Dict]]:
    prompt = _prompt(topic, audience, minutes, theme)
    raw = _call_gemini(prompt)
    try:
        data = json.loads(raw)
    except Exception:
        data = json.loads(_extract_json(raw))

    slides = data["slides"]
    slides = _normalize(slides, minutes)

    task_id = time.strftime("%Y%m%d_%H%M%S")
    (RAW_DIR / f"{task_id}.json").write_text(raw, encoding="utf-8")
    (CLEAN_DIR / f"{task_id}.json").write_text(json.dumps({"slides": slides}, indent=2), encoding="utf-8")
    return task_id, slides
