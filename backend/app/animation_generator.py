# backend/app/animation_generator.py
"""
Generates interactive animation metadata for lectures using Gemini AI.
Creates step-by-step animated learning experiences.
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
import google.generativeai as genai

from .models.animations import (
    LectureAnimations, SlideAnimation, AnimationStep,
    InteractionPoint, AnimationElement, AnimationType, InteractionType
)


API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in environment.")

genai.configure(api_key=API_KEY)
MODEL_NAME = "gemini-2.0-flash-exp"
GENERATION_CONFIG = {
    "response_mime_type": "application/json",
    "temperature": 0.7,
    "top_p": 0.95
}

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output" / "animations"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _animation_prompt(
    topic: str,
    audience: str,
    minutes: int,
    theme: str,
    interaction_level: str = "medium",
    animation_style: str = "dynamic"
) -> str:
    """Generate prompt for animation metadata."""
    
    interaction_guidance = {
        "low": "1-2 simple click-to-reveal interactions per slide",
        "medium": "2-3 varied interactions (click, quiz, drag) per slide",
        "high": "4-5 rich interactions including simulations and multi-step challenges"
    }
    
    animation_pacing = {
        "gentle": "slow, calm animations (1500-2000ms), suitable for younger learners",
        "dynamic": "moderate pace (800-1200ms), engaging and clear",
        "professional": "quick, efficient (500-800ms), respects learners' time"
    }
    
    return f"""
You are an expert educational content designer specializing in interactive, animated learning experiences.

Create a structured interactive lecture with step-by-step animations that transform passive viewing into active learning.

**Topic**: {topic}
**Audience**: {audience}
**Target duration**: {minutes} minutes
**Visual theme**: {theme}
**Animation style**: {animation_style} - {animation_pacing[animation_style]}
**Interaction level**: {interaction_level} - {interaction_guidance[interaction_level]}

**Your task**:
Generate 6-8 slides, each with:
1. **Animation Steps**: Break down each concept into 3-6 visual steps that build upon each other
2. **Interactive Elements**: Add user interactions that make learning active
3. **Audio Sync**: Timing for voiceover alignment
4. **Visual Elements**: Specific shapes, diagrams, text, arrows that animate

**Animation Types Available**:
- fade_in, slide_in, scale_up, draw, typewriter, bounce, rotate, morph, particle, highlight

**Interaction Types Available**:
- click_to_reveal: User clicks to reveal next element
- drag_and_drop: Drag elements to correct positions
- hover_info: Hover for additional information
- multiple_choice: Quiz question with options
- simulation: Interactive simulation (e.g., adjust slider to see effect)
- auto_advance: Automatically proceeds after animation

**Theme-Specific Effects**:
- Chalkboard: Chalk dust particles, hand-drawn style, white text on dark
- Minimalist: Clean fades, simple geometry, lots of whitespace
- Neon: Glow effects, vibrant colors, dynamic motion
- Corporate: Professional blues, smooth transitions, data-focused
- Paper: Sketch-like, textured backgrounds, warm colors
- Gradient: Colorful, modern, flowing animations

**Example Slide Structure**:
{{
  "slide_index": 0,
  "title": "Introduction to Photosynthesis",
  "concept": "Plants convert sunlight into energy",
  "difficulty": "medium",
  "estimated_time_seconds": 45,
  "steps": [
    {{
      "step_number": 1,
      "description": "Show plant with sunlight hitting leaves",
      "elements": [
        {{
          "id": "sun_1",
          "type": "icon",
          "content": "Sun icon",
          "position": {{"x": 20, "y": 20}},
          "style": {{"color": "yellow", "size": "large"}}
        }},
        {{
          "id": "plant_1",
          "type": "image",
          "content": "Plant illustration",
          "position": {{"x": 50, "y": 60}}
        }}
      ],
      "animation_type": "fade_in",
      "duration_ms": 1000,
      "delay_ms": 0,
      "narration_text": "Plants need sunlight to survive"
    }},
    {{
      "step_number": 2,
      "description": "Animate light rays traveling to leaf",
      "elements": [
        {{
          "id": "rays_1",
          "type": "arrow",
          "content": "Light rays",
          "position": {{"x": 25, "y": 30}}
        }}
      ],
      "animation_type": "draw",
      "duration_ms": 1200,
      "delay_ms": 500,
      "narration_text": "Sunlight travels to the leaves"
    }}
  ],
  "interactions": [
    {{
      "id": "click_leaf",
      "type": "click_to_reveal",
      "prompt": "Click on the leaf to see what happens inside",
      "target_element_id": "plant_1",
      "position": {{"x": 50, "y": 60}},
      "success_message": "Great! Let's zoom into the chloroplast",
      "unlocks_step": 3
    }},
    {{
      "id": "quiz_1",
      "type": "multiple_choice",
      "prompt": "What does the plant need for photosynthesis?",
      "options": ["Sunlight only", "Sunlight, water, and CO2", "Water only", "Soil only"],
      "correct_answer": "Sunlight, water, and CO2",
      "position": {{"x": 50, "y": 85}},
      "success_message": "Correct! All three are essential.",
      "hint": "Think about what enters and exits the leaf"
    }}
  ],
  "theme_effects": {{
    "chalkboard": {{"particle_effect": "chalk_dust", "text_style": "handwritten"}},
    "minimalist": {{"transition": "smooth_fade", "colors": "monochrome"}}
  }}
}}

**Requirements**:
1. Each slide must have 3-6 animation steps that build the concept progressively
2. Include {interaction_guidance[interaction_level]}
3. Steps should have logical timing (earlier steps get longer duration)
4. Position elements strategically (avoid overlap, use canvas space effectively)
5. Interactions should be meaningful, not decorative
6. Total estimated time should be ~{minutes * 60} seconds (±15%)
7. Return ONLY valid JSON (no markdown, no commentary)

**Output Format**:
{{
  "slides": [
    // Array of SlideAnimation objects as shown above
  ]
}}
"""


def _call_gemini(prompt: str) -> str:
    """Call Gemini API with the prompt."""
    model = genai.GenerativeModel(MODEL_NAME, generation_config=GENERATION_CONFIG)
    response = model.generate_content(prompt)
    return (response.text or "").strip()


def _extract_json(raw: str) -> str:
    """Extract JSON from response that might have markdown wrappers."""
    s, e = raw.find("{"), raw.rfind("}")
    if s == -1 or e == -1:
        raise ValueError("No JSON found in response")
    return raw[s:e+1]


def _normalize_timings(slides: List[Dict], target_minutes: int):
    """Normalize slide timings to match target duration."""
    total_time = sum(s.get("estimated_time_seconds", 30) for s in slides)
    target_seconds = target_minutes * 60
    
    if total_time > 0:
        scale = target_seconds / total_time
        for slide in slides:
            slide["estimated_time_seconds"] = int(
                slide.get("estimated_time_seconds", 30) * scale
            )


def generate_animations(
    topic: str,
    audience: str,
    minutes: int,
    theme: str,
    interaction_level: str = "medium",
    animation_style: str = "dynamic",
    task_id: str = None
) -> Tuple[str, LectureAnimations]:
    """
    Generate interactive animation metadata for a lecture.
    
    Returns:
        Tuple of (task_id, LectureAnimations object)
    """
    import time
    if not task_id:
        task_id = time.strftime("%Y%m%d_%H%M%S")
    
    print(f"[ANIMATIONS] Generating for '{topic}' ({minutes} min, {interaction_level} interaction)")
    
    # Generate animation metadata
    prompt = _animation_prompt(topic, audience, minutes, theme, interaction_level, animation_style)
    raw_response = _call_gemini(prompt)
    
    # Parse response
    try:
        data = json.loads(raw_response)
    except Exception:
        data = json.loads(_extract_json(raw_response))
    
    slides_data = data.get("slides", [])
    
    # Normalize timings
    _normalize_timings(slides_data, minutes)
    
    # Calculate totals
    total_time = sum(s.get("estimated_time_seconds", 30) for s in slides_data)
    total_interactions = sum(len(s.get("interactions", [])) for s in slides_data)
    
    # Create LectureAnimations object
    lecture_animations = LectureAnimations(
        lecture_id=task_id,
        topic=topic,
        audience=audience,
        theme=theme,
        slides=[SlideAnimation(**slide) for slide in slides_data],
        total_estimated_time_seconds=total_time,
        interaction_count=total_interactions,
        gamification={
            "total_points": total_interactions * 10,
            "badges": ["Engaged Learner", "Concept Master", "Quiz Champion"],
            "progress_tracking": True
        }
    )
    
    # Save to file
    output_file = OUTPUT_DIR / f"{task_id}.json"
    output_file.write_text(
        lecture_animations.model_dump_json(indent=2),
        encoding="utf-8"
    )
    
    print(f"[ANIMATIONS] Generated {len(slides_data)} slides with {total_interactions} interactions")
    print(f"[ANIMATIONS] Saved to: {output_file}")
    
    return task_id, lecture_animations


def load_animations(task_id: str) -> LectureAnimations:
    """Load animation data from file."""
    file_path = OUTPUT_DIR / f"{task_id}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Animation data not found for task {task_id}")
    
    data = json.loads(file_path.read_text(encoding="utf-8"))
    return LectureAnimations(**data)
