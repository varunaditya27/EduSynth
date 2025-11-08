"""Dual content generator for expanded educational content."""
from __future__ import annotations

import asyncio
import json
import logging
import re
from difflib import SequenceMatcher
from typing import Optional, List, Dict, Any

from google.generativeai import GenerativeModel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Optional import with a safe fallback
# ---------------------------------------------------------------------
try:
    from .text_utils import deduplicate_content  # type: ignore
except Exception:
    def _norm(s: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", (s or "").lower())).strip()

    def _is_near_dup(a: str, b: str, thresh: float = 0.9) -> bool:
        return SequenceMatcher(None, _norm(a), _norm(b)).ratio() >= thresh

    def deduplicate_content(
        narrative: str | list[str],
        key_concepts: List[str],
        supporting_details: List[str],
    ) -> tuple[str, List[str], List[str]]:
        """Simple built-in de-dup if text_utils is unavailable."""
        if isinstance(narrative, list):
            narrative_text = " ".join(narrative)
        else:
            narrative_text = narrative or ""
        # Sentences we consider "seen"
        seen_units: list[str] = []
        for chunk in re.split(r"[.!?]\s+", narrative_text):
            if chunk.strip():
                seen_units.append(chunk.strip())

        def _filter(items: List[str]) -> List[str]:
            out: List[str] = []
            for it in items or []:
                if not it or not it.strip():
                    continue
                keep = True
                for s in seen_units:
                    if _is_near_dup(it, s):
                        keep = False
                        break
                if keep:
                    # also de-dup against items we already kept
                    for kept in out:
                        if _is_near_dup(it, kept):
                            keep = False
                            break
                if keep:
                    out.append(it.strip())
            return out

        kc = _filter(key_concepts or [])
        sd = _filter(supporting_details or [])
        return narrative_text, kc, sd


class DualContentGenerator:
    """Generates both concise and expanded content for slides."""

    def __init__(self, model: GenerativeModel, level: str = "detailed"):
        """
        Args:
            model: Gemini model instance (google.generativeai.GenerativeModel)
            level: "basic" | "detailed" | "comprehensive"
        """
        self.model = model
        self.level = level

    # -----------------------------------------------------------------
    # Prompt build
    # -----------------------------------------------------------------
    def _build_dual_content_prompt(self, topic: str, title: str, points: List[str]) -> str:
        detail_levels = {
            "basic": "brief, foundational overview",
            "detailed": "thorough explanation with practical examples",
            "comprehensive": "in-depth analysis with theory and practice",
        }
        detail_desc = detail_levels.get(self.level, detail_levels["detailed"])

        bullets = "\n".join(f"- {p}" for p in (points or []))

        prompt = f"""You are a pedagogy-focused writing assistant.

Generate distinct educational content sections about "{title}" under the broader topic "{topic}".

The current slide points are:
{bullets}

Create three STRICTLY DISTINCT sections with NO content overlap:

1) Main Narrative (1–2 paragraphs)
- Cohesive {detail_desc}
- Full sentences, paragraph form
- NO bullet points
- Do NOT repeat content used elsewhere

2) Key Concepts (3–6 bullets)
- Each bullet ≤ 16 words
- Concept-label style (not full sentences)
- Add NEW info not in Narrative
- Focus on core principles/terminology
- Do NOT reuse text from other sections

3) Supporting Details (3–6 bullets)
- Add NEW info (examples, analogies, edge cases, pitfalls, mnemonics)
- Practical insights that extend the key concepts
- Do NOT repeat Narrative or Key Concepts

Return ONLY a valid JSON object matching this structure (no extra prose):

{{
  "expanded_content": ["<paragraph 1>", "<paragraph 2 (optional)>"],
  "key_concepts": ["<label bullet 1>", "<label bullet 2>", "..."],
  "supporting_details": ["<example bullet 1>", "<pitfall bullet 2>", "..."]
}}
"""
        return prompt

    # -----------------------------------------------------------------
    # Model call + parsing
    # -----------------------------------------------------------------
    async def _generate_raw_text(self, prompt: str, generation_config: dict) -> str:
        """Call Gemini in async context; supports async or sync models."""
        if hasattr(self.model, "generate_content_async"):
            resp = await self.model.generate_content_async(
                prompt, generation_config=generation_config
            )
        else:
            loop = asyncio.get_running_loop()
            resp = await loop.run_in_executor(
                None, lambda: self.model.generate_content(prompt, generation_config=generation_config)
            )

        text = getattr(resp, "text", None)
        if not text and hasattr(resp, "candidates") and resp.candidates:
            # very defensive extraction
            parts = getattr(resp.candidates[0].content, "parts", None)
            if parts and hasattr(parts[0], "text"):
                text = parts[0].text
        return text or ""

    @staticmethod
    def _strip_code_fences(s: str) -> str:
        s = s.strip()
        # Remove ```json ... ``` or ``` ... ```
        if s.startswith("```"):
            s = re.sub(r"^```(?:json)?\s*", "", s)
            s = re.sub(r"\s*```$", "", s)
        return s.strip()

    @staticmethod
    def _safe_load_json(s: str) -> Dict[str, Any]:
        s = DualContentGenerator._strip_code_fences(s)
        # Try exact JSON first
        try:
            return json.loads(s)
        except Exception:
            pass
        # Try to extract JSON object substring
        m = re.search(r"\{.*\}", s, flags=re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        raise ValueError("Model did not return valid JSON.")

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------
    async def generate_dual_content(
        self,
        topic: str,
        title: str,
        points: List[str],
        force_refresh: bool = False,  # kept for API symmetry, not used here
    ) -> Dict[str, Any]:
        """
        Returns:
            {
              "expanded_content": str | List[str],
              "key_concepts": List[str],
              "supporting_details": List[str]
            }
        """
        generation_config = {
            "temperature": 0.4,
            "max_output_tokens": 2048,
            "top_p": 0.8,
            "top_k": 40,
        }

        prompt = self._build_dual_content_prompt(topic, title, points)

        try:
            raw = await self._generate_raw_text(prompt, generation_config)
            parsed = self._safe_load_json(raw)

            # Required fields
            for f in ("expanded_content", "key_concepts", "supporting_details"):
                if f not in parsed:
                    raise ValueError(f"Response missing required field: {f}")

            expanded_content = parsed["expanded_content"]
            key_concepts = parsed["key_concepts"] or []
            supporting_details = parsed["supporting_details"] or []

            # Normalize narrative as string (pdf_enhanced supports both)
            narrative = (
                " ".join(expanded_content)
                if isinstance(expanded_content, list)
                else (expanded_content or "")
            )

            # De-dup across sections
            narrative, filtered_concepts, filtered_details = deduplicate_content(
                narrative=narrative,
                key_concepts=key_concepts,
                supporting_details=supporting_details,
            )

            logger.debug(
                "De-dup for '%s': kept %d/%d concepts, %d/%d details",
                title,
                len(filtered_concepts), len(key_concepts),
                len(filtered_details), len(supporting_details),
            )

            # Enforce bounds
            filtered_concepts = filtered_concepts[:6]
            filtered_details = filtered_details[:6]

            return {
                "expanded_content": narrative.strip(),
                "key_concepts": filtered_concepts,
                "supporting_details": filtered_details,
            }

        except Exception as e:
            logger.error("Failed to generate content for '%s': %s", title, e)
            # Fallback: compress points into narrative and produce short extras
            pts = [p for p in (points or []) if p]
            fallback_narr = " ".join(pts)[:800] if pts else f"{title} — {topic}"
            return {
                "expanded_content": fallback_narr,
                "key_concepts": pts[:3],
                "supporting_details": (
                    [f"Example/analogy for: {pts[0]}", f"Pitfall related to: {pts[-1]}"]
                    if len(pts) >= 2 else []
                ),
            }
