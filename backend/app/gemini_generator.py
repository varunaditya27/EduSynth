import os
import json
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

import google.generativeai as genai


# ---------------------------
# Config
# ---------------------------
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    # The /generate route will surface this as a 500 with message from the raise.
    raise RuntimeError("GEMINI_API_KEY not found in environment. Set it before calling generate_slides().")

# Configure Gemini client
# response_mime_type hints the model to return clean JSON.
genai.configure(api_key=API_KEY)
GENERATION_CONFIG = {
    "response_mime_type": "application/json",
    "temperature": 0.5,
    "top_p": 0.9,
}

MODEL_NAME = "gemini-2.5-pro"  # Safer, widely available


# ---------------------------
# Paths
# ---------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = REPO_ROOT / "ai_generation" / "prompt_template.txt"
RAW_DIR = REPO_ROOT / "ai_generation" / "output" / "raw_gemini"
CLEAN_DIR = REPO_ROOT / "ai_generation" / "output" / "slides"

RAW_DIR.mkdir(parents=True, exist_ok=True)
CLEAN_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------
# Helpers
# ---------------------------
def _read_prompt_template() -> str:
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"Prompt template not found at {PROMPT_PATH.as_posix()}")
    return PROMPT_PATH.read_text(encoding="utf-8")


def _build_prompt(template: str, topic: str, audience: str, minutes: int, theme: str) -> str:
    # Avoid .format() because of JSON braces in the template
    return (
        template
        .replace("{topic}", str(topic))
        .replace("{audience}", str(audience))
        .replace("{minutes}", str(minutes))
        .replace("{theme}", str(theme))
    )


def _call_gemini(prompt: str) -> str:
    model = genai.GenerativeModel(MODEL_NAME, generation_config=GENERATION_CONFIG)
    resp = model.generate_content(prompt)
    # Prefer .text; fallback to candidates if needed
    raw = (getattr(resp, "text", None) or "").strip()
    if not raw and getattr(resp, "candidates", None):
        parts = resp.candidates[0].content.parts
        raw = "".join(getattr(p, "text", "") for p in parts if getattr(p, "text", None)).strip()
    if not raw:
        raise ValueError("Empty response from Gemini.")
    return raw


def _extract_json_text(raw_text: str) -> str:
    """
    Extract the JSON object from the model output.
    Finds the first '{' and the last '}' and slices between.
    """
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model response.")
    return raw_text[start:end + 1]


def _word_count(s: str) -> int:
    return len(re.findall(r"\w+", s or ""))


def _slide_count_for_minutes(minutes: int) -> int:
    # Your team rule of thumb
    if minutes <= 3:
        return 5
    if minutes <= 5:
        return 6
    return 7


def _validate_and_normalize(slides: List[Dict[str, Any]], minutes: int) -> List[Dict[str, Any]]:
    """
    Enforce schema shape and pacing.
    - Ensure indices 0..n-1
    - Title non-empty, <= ~60 chars
    - Points 2–4 short strings
    - Narration trimmed to ~80 words
    - Duration 8–20 seconds typical
    - Total duration ≈ minutes*60 within ±10% (scale if needed)
    """
    if not isinstance(slides, list) or not slides:
        raise ValueError("`slides` must be a non-empty array.")

    target_count = _slide_count_for_minutes(minutes)
    # If out of range, clip or pad (pad is rare; better to clip).
    if len(slides) > 7:
        slides = slides[:7]
    if len(slides) < 5:
        # Not ideal; we accept but warn by normalizing durations later.
        pass
    if target_count in (5, 6, 7) and len(slides) not in (5, 6, 7):
        # We won't hard error; we just proceed with what we have.
        pass

    # Normalize fields
    fixed: List[Dict[str, Any]] = []
    for idx, s in enumerate(slides):
        title = str(s.get("title", "")).strip()
        if not title:
            title = f"Slide {idx + 1}"
        if len(title) > 60:
            title = title[:57].rstrip() + "..."

        points = s.get("points", [])
        if not isinstance(points, list):
            points = []
        # Keep 2–4 short bullets; trim length
        cleaned_points = []
        for p in points:
            p = str(p).strip()
            if not p:
                continue
            if len(p) > 80:
                p = p[:77].rstrip() + "..."
            cleaned_points.append(p)
        if len(cleaned_points) < 2:
            # synthesize short bullets from title if too few
            cleaned_points = cleaned_points + [f"Key idea: {title}", "Main takeaway"]
        cleaned_points = cleaned_points[:4]

        narration = str(s.get("narration", "")).strip()
        if not narration:
            # derive quick narration from title + bullets
            narration = f"{title}. " + " ".join(cleaned_points)
        # Trim narration to ~80 words
        words = narration.split()
        if len(words) > 80:
            # trim to nearest sentence boundary under 80 words if possible
            truncated = " ".join(words[:80])
            m = re.search(r"(.+[.!?])\s+\S*$", truncated)
            narration = m.group(1) if m else truncated

        # Duration handling
        try:
            duration = float(s.get("duration", 0))
        except Exception:
            duration = 0.0
        if duration <= 0:
            # Estimate from word count at ~2.3 w/s
            est = max(8.0, min(20.0, _word_count(narration) / 2.3))
            duration = float(f"{est:.1f}")
        # Clamp per-slide
        duration = max(8.0, min(20.0, duration))

        fixed.append({
            "index": idx,  # reindex to 0..n-1
            "title": title,
            "points": cleaned_points,
            "narration": narration,
            "duration": float(f"{duration:.1f}"),
        })

    # Scale durations to hit target total within ±10%
    target_total = max(30, int(minutes) * 60)  # guard tiny minutes
    current_total = sum(s["duration"] for s in fixed) or 1.0
    lower, upper = 0.9 * target_total, 1.1 * target_total

    if current_total < lower or current_total > upper:
        scale = target_total / current_total
        # Proportional scaling
        for s in fixed:
            s["duration"] = float(f"{max(8.0, min(20.0, s['duration'] * scale)):.1f}")
        # Second pass to force exact total while staying reasonable
        current_total = sum(s["duration"] for s in fixed)
        if current_total != target_total and current_total > 0:
            delta = target_total - current_total
            per = delta / len(fixed)
            for s in fixed:
                s["duration"] = float(f"{max(8.0, min(20.0, s['duration'] + per)):.1f}")

    # Final reindex (in case of any adjustments)
    for i, s in enumerate(fixed):
        s["index"] = i

    return fixed


def _make_task_id() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


# ---------------------------
# Public API
# ---------------------------
def generate_slides(topic: str, audience: str, minutes: int, theme: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Orchestrates:
      - Prompt building
      - Gemini call
      - JSON parsing with fallback
      - Validation & normalization
      - Save raw and cleaned outputs
      - Return (task_id, slides)
    """
    template = _read_prompt_template()
    prompt = _build_prompt(template, topic, audience, minutes, theme)

    # First attempt
    raw_text = _call_gemini(prompt)

    # Parse robustly
    try:
        data = json.loads(raw_text)
    except Exception:
        # Fallback extract JSON object
        extracted = _extract_json_text(raw_text)
        try:
            data = json.loads(extracted)
            raw_text = extracted  # prefer the clean JSON for saving raw
        except Exception as e:
            # Retry once with a formatting fix prompt
            fix_prompt = (
                "Your last response was not valid JSON. "
                "Reformat the same content as valid JSON only, no markdown, no text."
            )
            raw_retry = _call_gemini(prompt + "\n\n" + fix_prompt)
            extracted_retry = _extract_json_text(raw_retry)
            data = json.loads(extracted_retry)
            raw_text = extracted_retry

    if "slides" not in data or not isinstance(data["slides"], list):
        raise ValueError("Model output missing `slides` array.")

    slides = _validate_and_normalize(data["slides"], minutes)

    # Save artifacts
    task_id = _make_task_id()
    (RAW_DIR / f"{task_id}.json").write_text(raw_text, encoding="utf-8")
    (CLEAN_DIR / f"{task_id}.json").write_text(json.dumps({"slides": slides}, indent=2), encoding="utf-8")

    return task_id, slides
