"""
Slide deck content schemas with strict validation.
"""
from pydantic import BaseModel, Field, conlist
from typing import List, Optional, Literal

DiagramType = Literal["process", "tree", "timeline", "compare"]


class SlideItem(BaseModel):
    """Individual slide content structure."""
    index: int
    title: str = Field(min_length=1, max_length=80)
    points: conlist(str, min_length=1, max_length=5)
    diagram: Optional[DiagramType] = None


class LecturePlan(BaseModel):
    """Complete lecture plan with slides and metadata."""
    topic: str
    language: str = "en"
    theme: Literal["minimalist", "chalkboard", "corporate"] = "minimalist"
    duration_minutes: int
    slides: conlist(SlideItem, min_length=2, max_length=30)
    orientation: Optional[Literal["auto", "portrait", "landscape"]] = "auto"
    device_preset: Optional[Literal["desktop", "tablet", "mobile"]] = None