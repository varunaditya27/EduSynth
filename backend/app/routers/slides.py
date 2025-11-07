"""
Slide Deck API routes.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status

from app.deps.auth import CurrentUser, get_current_user
from app.models.slides import (
    GenerateSlidesRequest,
    JobQueuedResponse,
    JobStatusResponse,
    DeckResponse
)
from app.services.slides.generator import (
    enqueue_generation_job,
    get_job_status,
    get_deck,
)

router = APIRouter()


# ===========================
# ENDPOINTS
# ===========================

@router.post("/generate", response_model=JobQueuedResponse)
async def generate_slides(
    request: GenerateSlidesRequest,
    user: CurrentUser = Depends(get_current_user),
) -> JobQueuedResponse:
    """
    Queue a new slide deck generation job.
    
    Args:
        request: Slide deck configuration
        user: Authenticated user
        
    Returns:
        Job ID and queued status
    """
    job_id = await enqueue_generation_job(user.user_id, request)
    return JobQueuedResponse(job_id=job_id, status="QUEUED")


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(
    job_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> JobStatusResponse:
    """
    Get the status of a generation job.
    
    Args:
        job_id: Job identifier
        user: Authenticated user
        
    Returns:
        Current job status and progress
    """
    status_data = await get_job_status(user.user_id, job_id)
    return JobStatusResponse(**status_data)


@router.get("/{deck_id}", response_model=DeckResponse)
async def get_deck_info(
    deck_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> DeckResponse:
    """
    Get information about a completed slide deck.
    
    Args:
        deck_id: Deck identifier
        user: Authenticated user
        
    Returns:
        Deck metadata and download URLs
    """
    deck_data = await get_deck(user.user_id, deck_id)
    return DeckResponse(**deck_data)