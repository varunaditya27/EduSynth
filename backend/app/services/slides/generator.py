# backend/app/services/slides/generator.py

from typing import Dict, Optional
from datetime import datetime

from app.models.slides import GenerateSlidesRequest
from app.db import get_client


async def enqueue_generation_job(
    user_id: str,
    req: GenerateSlidesRequest
) -> str:
    """
    Create a new generation job in the database and return its ID.
    Job is created with QUEUED status and will be processed asynchronously.
    
    Args:
        user_id: ID of the user requesting generation
        req: Generation request parameters
        
    Returns:
        job_id: UUID of the created job
    """
    db = get_client()
    
    # Create generation job record
    job = await db.generationjob.create(
        data={
            "user_id": user_id,
            "status": "QUEUED",
            "progress_pct": 0
        }
    )
    
    # TODO: Enqueue actual background job for processing
    # - Generate outline based on topic, audience, duration
    # - For each slide, search Unsplash for relevant image
    # - Assemble PPTX/PDF with python-pptx or similar
    # - Upload final file to R2
    # - Update job status to COMPLETED with deck_id
    
    return job.id


async def get_job_status(
    user_id: str,
    job_id: str
) -> Optional[Dict]:
    """
    Retrieve the current status of a generation job.
    
    Args:
        user_id: ID of the user (for authorization)
        job_id: ID of the job to check
        
    Returns:
        Dictionary with job status fields, or None if not found/unauthorized
    """
    db = get_client()
    
    # Fetch job scoped to user
    job = await db.generationjob.find_first(
        where={
            "id": job_id,
            "user_id": user_id
        }
    )
    
    if not job:
        return None
    
    # Format error message if present
    error_msg = None
    if job.error_code or job.error_message:
        error_msg = f"{job.error_code}: {job.error_message}" if job.error_code else job.error_message
    
    return {
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress_pct,
        "deck_id": job.deck_id,
        "error": error_msg
    }


async def get_deck(
    user_id: str,
    deck_id: str
) -> Optional[Dict]:
    """
    Retrieve metadata for a specific slide deck.
    
    Args:
        user_id: ID of the user (for authorization)
        deck_id: ID of the deck to retrieve
        
    Returns:
        Dictionary with deck metadata fields, or None if not found/unauthorized
    """
    db = get_client()
    
    # Fetch deck scoped to user
    deck = await db.slidedeck.find_first(
        where={
            "id": deck_id,
            "user_id": user_id
        }
    )
    
    if not deck:
        return None
    
    # TODO: Generate presigned URLs for download and thumbnail
    # from app.clients.r2 import R2Client
    # r2 = R2Client()
    # download_url = await r2.generate_presigned_url(deck.r2_key)
    # thumbnail_url = await r2.generate_presigned_url(deck.cover_thumb_r2_key) if deck.cover_thumb_r2_key else None
    
    return {
        "deck_id": deck.id,
        "topic": deck.topic,
        "theme": deck.theme,
        "slide_count": deck.slide_count,
        "format": deck.format,
        "download_url": None,  # TODO: Generate from R2
        "thumbnail_url": None,  # TODO: Generate from R2
        "created_at": deck.created_at
    }