# backend/app/gemini_utils.py
import uuid
import json
from typing import Dict
from pathlib import Path
from .schema import SlidesPayload

OUTDIR = Path(__file__).resolve().parent.parent / "output"

def generate_mock_slides(task_id: str, topic: str, audience: str, length: str, theme: str) -> Dict:
    # A deterministic mock of what Gemini should produce
    slides = [
        {
            "index": 0,
            "title": f"Intro: {topic}",
            "points": [
                f"What is {topic}?",
                f"Why {topic} matters for {audience}"
            ],
            "narration": f"Hello! In this lesson we will explore {topic} and why it's important for {audience}.",
            "duration": 10.0
        },
        {
            "index": 1,
            "title": f"Core Concepts of {topic}",
            "points": [
                "Key concept 1",
                "Key concept 2"
            ],
            "narration": f"Now let's break down the core ideas behind {topic}.",
            "duration": 12.0
        },
        {
            "index": 2,
            "title": "Summary & Next Steps",
            "points": [
                "Recap main points",
                "Suggested practice / quiz"
            ],
            "narration": f"To summarize, we've covered the essentials of {topic}. Try a short exercise to solidify learning.",
            "duration": 8.0
        }
    ]

    payload = {"slides": slides}
    # ensure output folder exists
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "raw_gemini").mkdir(exist_ok=True)
    (OUTDIR / "slides").mkdir(exist_ok=True)

    raw_path = OUTDIR / "raw_gemini" / f"{task_id}.json"
    cleaned_path = OUTDIR / "slides" / f"{task_id}.json"

    raw_path.write_text(json.dumps({"mock": True, "payload": payload}, indent=2), encoding="utf-8")
    cleaned_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return payload
