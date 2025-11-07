"""
Slide deck generation service - DB operations only (no generation logic yet).
"""
from typing import Optional
from datetime import datetime
from fastapi import HTTPException

from app.db import get_client
from app.models.slides import GenerateSlidesRequest


async def enqueue_generation_job(
    user_id: str,
    request: GenerateSlidesRequest,
) -> str:
    """
    Create a new generation job in the database.
    
    Args:
        user_id: Authenticated user ID
        request: Slide deck configuration
        
    Returns:
        Created job ID
    """
    db = await get_client()
    
    # Ensure user exists (upsert with placeholder email if needed)
    await db.user.upsert(
        where={"id": user_id},
        data={
            "create": {
                "id": user_id,
                "email": f"{user_id}@placeholder.local",
            },
            "update": {},
        },
    )
    
    # Create generation job with QUEUED status
    job = await db.generationjob.create(
        data={
            "userId": user_id,
            "status": "QUEUED",
            "progressPct": 0,
        }
    )
    
    # TODO: Trigger actual generation workflow (background task, queue, etc.)
    
    return job.id


async def get_job_status(user_id: str, job_id: str) -> dict:
    """
    Retrieve the status of a generation job.
    
    Args:
        user_id: Authenticated user ID
        job_id: Job identifier
        
    Returns:
        Dictionary matching JobStatusResponse shape
        
    Raises:
        HTTPException: 404 if job not found or doesn't belong to user
    """
    db = await get_client()
    
    # Fetch job scoped by user_id
    job = await db.generationjob.find_first(
        where={
            "id": job_id,
            "userId": user_id,
        }
    )
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Map database status to API status
    # DB statuses: QUEUED, PROCESSING, COMPLETED, FAILED
    # API statuses: QUEUED, GENERATING, UPLOADING, READY, FAILED
    status_map = {
        "QUEUED": "QUEUED",
        "PROCESSING": "GENERATING",
        "COMPLETED": "READY",
        "FAILED": "FAILED",
    }
    
    api_status = status_map.get(job.status, "QUEUED")
    
    return {
        "job_id": job.id,
        "status": api_status,
        "progress": job.progressPct,
        "deck_id": job.deckId,
        "error": job.errorMessage if job.status == "FAILED" else None,
    }

async def get_deck(user_id: str, deck_id: str) -> dict:
    """
    Get information about a generated slide deck.
    
    Args:
        user_id: Authenticated user ID
        deck_id: Deck identifier
        
    Returns:
        Dictionary matching DeckResponse shape
        
    Raises:
        HTTPException: 404 if deck not found or doesn't belong to user
    """
    db = await get_client()
    
    # Fetch deck scoped by user_id
    deck = await db.slidedeck.find_first(
        where={
            "id": deck_id,
            "userId": user_id,
        }
    )
    
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    return {
        "deck_id": deck.id,
        "topic": deck.topic,
        "theme": deck.theme,
        "slide_count": len(deck.slides),
        "format": deck.format,
        "download_url": deck.download_url,
        "thumbnail_url": deck.thumbnail_url,
        "created_at": deck.created_at,
    }


async def get_deck(user_id: str, deck_id: str) -> dict:
    """
    Retrieve a slide deck's metadata.
    
    Args:
        user_id: Authenticated user ID
        deck_id: Deck identifier
        
    Returns:
        Dictionary matching DeckResponse shape
        
    Raises:
        HTTPException: 404 if deck not found or doesn't belong to user
    """
    db = await get_client()
    
    # Fetch deck scoped by user_id
    deck = await db.slidedeck.find_first(
        where={
            "id": deck_id,
            "userId": user_id,
        }
    )
    
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    # TODO: Generate actual download URLs using R2 presigned URLs
    # TODO: Generate thumbnail URLs if cover_thumb_r2_key exists
    
    return {
        "deck_id": deck.id,
        "topic": deck.topic,
        "theme": deck.theme,
        "slide_count": deck.slideCount,
        "format": deck.format,
        "download_url": None,  # TODO: Generate presigned URL
        "thumbnail_url": None,  # TODO: Generate thumbnail URL
        "created_at": deck.createdAt,
    }