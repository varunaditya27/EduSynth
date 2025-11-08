"""
Gemini-powered generator for PDF notes:
- Produces concise bullets for PPT (ppt_points)
- Produces expanded bullets (pdf_points)
- Produces paragraph notes (pdf_paragraphs)
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
import google.generativeai as genai

from .schemas.slides import LecturePlan, SlideItem
from .gemini_generator import (
    API_KEY, MODEL_NAME, GENERATION_CONFIG,
    RAW_DIR, CLEAN_DIR, _extract_json
)


# --- Text Utilities ----------------------------------------------------

def to_concise(items: List[str], max_words: int) -> List[str]:
    """Convert bullets to concise form (≤max_words each)."""
    def _truncate(s: str) -> str:
        words = s.split()
        if len(words) <= max_words:
            return s
        return ' '.join(words[:max_words]) + "..."

    return [_truncate(item) for item in items]


def to_expanded(items: List[str], max_words: int) -> List[str]:
    """Convert bullets to expanded form with more detail."""
    templates = [
        "Exploring {}: {}",
        "Key concept - {}: {}",
        "Understanding {}: {}",
        "Important aspect - {}: {}",
        "Deep dive into {}: {}",
    ]
    
    expanded = []
    for item in items:
        words = item.split()
        if len(words) <= 3:  # Very short bullet, needs expansion
            topic = ' '.join(words)
            detail = f"A fundamental concept in this lesson that helps us understand {topic}."
            template = templates[len(expanded) % len(templates)]
            expanded.append(template.format(topic, detail))
        elif len(words) >= max_words:
            expanded.append(item)  # Already long enough
        else:
            expanded.append(f"{item} - This demonstrates an important principle in the topic.")
    return expanded


def to_paragraphs(items: List[str]) -> List[str]:
    """Convert bullets to educational paragraphs with examples."""
    paragraphs = []
    
    # Introduction paragraph
    if items:
        first = items[0]
        intro = (
            f"Let's explore {first} in detail. This concept is fundamental to understanding "
            f"the topic and provides a strong foundation for what follows. "
            f"Think of it as building blocks that we'll use throughout this lesson."
        )
        paragraphs.append(intro)

    # Content paragraphs - group every 2-3 points
    chunk_size = min(3, max(2, len(items) // 2))
    for i in range(0, len(items), chunk_size):
        chunk = items[i:i+chunk_size]
        points = ". ".join(p.rstrip(".") for p in chunk)
        expanded = (
            f"{points}. These points illustrate key aspects that build upon each other. "
            f"Understanding their relationships helps grasp the bigger picture."
        )
        paragraphs.append(expanded)

    # Summary paragraph if we have enough content
    if len(items) > 3:
        summary = (
            "Taking all these points together, we can see how they form a comprehensive "
            "view of the topic. Each element contributes to our understanding and helps "
            "build a solid foundation for practical application."
        )
        paragraphs.append(summary)

    return paragraphs


# --- Gemini Prompting ------------------------------------------------

def _build_prompt(
    topic: str,
    audience: str,
    minutes: int,
    theme: str,
    max_words_ppt: int,
    max_words_pdf: int,
    slides_min: int,
    slides_max: int
) -> str:
    """Build a detailed prompt requesting dual-form content."""
    return f"""
You are an expert educational content designer creating a {minutes}-minute lecture on {topic}.
Your task is to generate content in both concise and expanded forms.

Topic: {topic}
Audience: {audience}
Theme: {theme}

Requirements:
1. Generate {slides_min}-{slides_max} slides with educational content suitable for {audience}.
2. For each slide, provide:
   - title (clear, informative)
   - ppt_points (3-6 bullet points, max {max_words_ppt} words each)
   - pdf_points (4-8 expanded bullets, max {max_words_pdf} words each)
   - pdf_paragraphs (2-3 paragraphs, each 2-4 sentences with examples/analogies)

Style guide:
- PPT points: Concise, memorable key ideas
- PDF points: Fuller explanations with context
- Paragraphs: Educational tone, clear examples, practical connections
- Language: Clear, define jargon, suitable for {audience}

Return strict JSON with this structure:
{{
  "slides": [
    {{
      "title": "string",
      "ppt_points": ["short bullet 1", "short bullet 2", ...],
      "pdf_points": ["detailed bullet 1", "detailed bullet 2", ...],
      "pdf_paragraphs": ["paragraph 1", "paragraph 2", ...]
    }},
    ...
  ]
}}
"""


# --- Main Generator -------------------------------------------------

async def generate_pdf_plan(
    topic: str,
    audience: str,
    minutes: int,
    theme: str,
    max_words_ppt: int = 14,
    max_words_pdf: int = 40,
    want_paragraphs: bool = True,
    slides_min: int = 5,
    slides_max: int = 9
) -> LecturePlan:
    """
    Generate a LecturePlan with dual-form content optimized for PDF output.
    Each slide contains both concise PPT points and expanded PDF content.
    """
    # Build and send prompt
    prompt = _build_prompt(
        topic, audience, minutes, theme,
        max_words_ppt, max_words_pdf,
        slides_min, slides_max
    )
    
    model = genai.GenerativeModel(MODEL_NAME, generation_config=GENERATION_CONFIG)
    raw_resp = model.generate_content(prompt).text or ""

    # Extract and parse JSON
    try:
        json_str = _extract_json(raw_resp)
        data = json.loads(json_str)
        raw_slides = data.get("slides", [])
    except Exception as e:
        print(f"JSON extraction failed: {e}")
        raw_slides = []

    # Process slides with fallbacks
    slides = []
    for idx, raw in enumerate(raw_slides):
        title = raw.get("title", f"Section {idx + 1}")
        
        # Gather all potential content
        ppt = raw.get("ppt_points", [])
        pdf = raw.get("pdf_points", [])
        base = raw.get("points", [])  # Legacy/fallback
        paragraphs = raw.get("pdf_paragraphs", [])

        # Ensure we have ppt_points
        if not ppt:
            if base:
                ppt = to_concise(base, max_words_ppt)
            elif pdf:
                ppt = to_concise(pdf, max_words_ppt)

        # Ensure we have pdf_points
        if not pdf:
            if base:
                pdf = to_expanded(base, max_words_pdf)
            elif ppt:
                pdf = to_expanded(ppt, max_words_pdf)

        # Generate paragraphs if wanted and missing
        if want_paragraphs and not paragraphs:
            source = pdf or ppt or base
            if source:
                paragraphs = to_paragraphs(source)

        # Create slide with all content forms
        slide = SlideItem(
            index=idx,
            title=title,
            points=ppt or pdf or base or ["Content being generated..."],
            ppt_points=ppt,
            pdf_points=pdf,
            pdf_paragraphs=paragraphs if want_paragraphs else None
        )
        slides.append(slide)

    # Write debug output
    task_id = time.strftime("%Y%m%d_%H%M%S")
    try:
        debug_data = {
            "prompt": prompt,
            "raw_response": raw_resp,
            "processed_slides": [s.dict() for s in slides]
        }
        (RAW_DIR / f"{task_id}_pdf.json").write_text(
            json.dumps(debug_data, indent=2),
            encoding="utf-8"
        )
    except Exception as e:
        print(f"Debug output failed: {e}")

    # Return complete plan
    return LecturePlan(
        topic=topic,
        theme=theme,
        duration_minutes=minutes,
        slides=slides,
        preferred_format="pdf"  # Signal that this was made for PDF
    )
