"""
Slide deck content schemas with strict validation.
Updated to support orientation and device presets for adaptive PPTX generation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Annotated
from typing_extensions import Annotated

DiagramType = Literal["process", "tree", "timeline", "compare"]


class SlideItem(BaseModel):
    """Individual slide content structure."""
    index: int
    title: str = Field(min_length=1, max_length=120)
    points: List[str] = Field(min_items=1, max_items=8)
    diagram: Optional[DiagramType] = None
    # Extended content for PDF version
    expanded_content: Optional[str] = None
    supporting_details: Optional[List[str]] = None
    key_concepts: Optional[List[str]] = None


class LecturePlan(BaseModel):
    """Complete lecture plan with slides and metadata."""
    topic: str
    language: str = "en"
    theme: Literal["minimalist", "chalkboard", "corporate"] = "minimalist"
    duration_minutes: int
    slides: List[SlideItem] = Field(min_items=1, max_items=60)

    # Presentation preferences for adaptive PPTX generation
    orientation: Optional[Literal["auto", "portrait", "landscape"]] = "auto"
    device_preset: Optional[Literal["desktop", "tablet", "mobile"]] = None
    preferred_format: Optional[Literal["pptx", "pdf"]] = "pptx"
    
    # Enhanced content preferences
    generate_expanded_content: bool = False  # Whether to generate expanded educational content
    expanded_content_level: Optional[Literal["basic", "detailed", "comprehensive"]] = "detailed"  # Detail level for expanded content