# backend/app/schema.py
from pydantic import BaseModel, Field
from typing import List

class Slide(BaseModel):
    index: int = Field(..., ge=0)
    title: str
    points: List[str]
    narration: str
    duration: float  # seconds

class SlidesPayload(BaseModel):
    slides: List[Slide]

