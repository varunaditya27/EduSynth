from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

class GenerateSlidesRequest(BaseModel):
    """Request payload for generating a new slide deck"""
    topic: str = Field(..., min_length=1, max_length=500)
    audience: Optional[str] = Field(None, max_length=200)
    duration_minutes: int = Field(..., ge=1, le=180)
    theme: Literal["minimalist", "chalkboard", "corporate"]
    preferred_format: Literal["pptx", "pdf"] = "pptx"
    language: str = Field(default="en", min_length=2, max_length=10)
    
    # Expanded content generation preferences
    generate_expanded_content: bool = False
    expanded_content_level: Optional[Literal["basic", "detailed", "comprehensive"]] = "detailed"
    force_refresh_content: bool = False

class JobQueuedResponse(BaseModel):
    """Response after successfully queuing a generation job"""
    job_id: str
    status: Literal["QUEUED"]

class JobStatusResponse(BaseModel):
    """Response containing job status and progress"""
    job_id: str
    status: Literal["QUEUED", "GENERATING", "UPLOADING", "READY", "FAILED"]
    progress: int
    deck_id: Optional[str] = None
    error: Optional[str] = None

class DeckResponse(BaseModel):
    """Response containing slide deck metadata"""
    deck_id: str
    topic: str
    theme: str
    slide_count: int
    format: str
    download_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: datetime