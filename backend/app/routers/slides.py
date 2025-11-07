# backend/app/routers/slides.py

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from app.deps.auth import get_current_user, CurrentUser
from app.models.slides import (
    GenerateSlidesRequest,
    JobQueuedResponse,
    JobStatusResponse,
    DeckResponse
)
from app.services.slides.generator import (
    enqueue_generation_job,
    get_job_status,
    get_deck
)

router = APIRouter()





# Endpoints

@router.post("/generate", response_model=JobQueuedResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_slides(
    request: GenerateSlidesRequest,
    current_user: CurrentUser = Depends(get_current_user)
) -> JobQueuedResponse:
    """
    Generate a new slide deck based on the provided parameters.
    Creates a generation job and returns immediately with job_id.
    
    Args:
        request: Slide generation parameters
        current_user: Authenticated user from JWT token
        
    Returns:
        JobQueuedResponse with job_id and initial status
    """
    job_id = await enqueue_generation_job(current_user.user_id, request)
    
    return JobQueuedResponse(
        job_id=job_id,
        status="QUEUED"
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_generation_job_status(
    job_id: str,
    current_user: CurrentUser = Depends(get_current_user)
) -> JobStatusResponse:
    """
    Get the status of a slide generation job.
    
    Args:
        job_id: ID of the generation job
        current_user: Authenticated user from JWT token
        
    Returns:
        JobStatusResponse with current status and progress
        
    Raises:
        HTTPException: 404 if job not found or doesn't belong to user
    """
    status, progress, deck_id, error = await get_job_status(job_id, current_user.user_id)
    
    if status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found or access denied"
        )
    
    return JobStatusResponse(
        job_id=job_id,
        status=status,
        progress=progress,
        deck_id=deck_id,
        error=error
    )

@router.get("/decks/{deck_id}", response_model=DeckResponse)
async def get_slide_deck(
    deck_id: str,
    current_user: CurrentUser = Depends(get_current_user)
) -> DeckResponse:
    """
    Get metadata and download URL for a generated slide deck.
    
    Args:
        deck_id: ID of the deck to retrieve
        current_user: Authenticated user from JWT token
        
    Returns:
        DeckResponse with metadata and download URL
        
    Raises:
        HTTPException: 404 if deck not found or access denied
    """
    deck_data = await get_deck(deck_id, current_user.user_id)
    
    if deck_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deck {deck_id} not found or access denied"
        )
    
    # Convert datetime string to datetime object if needed
    if isinstance(deck_data["created_at"], str):
        deck_data["created_at"] = datetime.fromisoformat(deck_data["created_at"].replace("Z", "+00:00"))
    
    return DeckResponse(**deck_data)
    job_data = await get_job_status(current_user.user_id, job_id)
    
    if not job_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found or access denied"
        )
    
    return JobStatusResponse(**job_data)


@router.get("/{deck_id}", response_model=DeckResponse)
async def get_slide_deck(
    deck_id: str,
    current_user: CurrentUser = Depends(get_current_user)
) -> DeckResponse:
    """
    Get metadata for a specific slide deck.
    
    Args:
        deck_id: ID of the slide deck
        current_user: Authenticated user from JWT token
        
    Returns:
        DeckResponse with deck metadata and URLs
        
    Raises:
        HTTPException: 404 if deck not found or doesn't belong to user
    """
    deck_data = await get_deck(current_user.user_id, deck_id)
    
    if not deck_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deck {deck_id} not found or access denied"
        )
    
    return DeckResponse(**deck_data)