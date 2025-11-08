"""
Slide Deck API routes with PPTX and PDF export.
"""
import logging
import uuid
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.deps.auth import CurrentUser, get_current_user
from app.models.slides import (
    GenerateSlidesRequest,
    JobQueuedResponse,
    JobStatusResponse,
    DeckResponse,
)
from app.schemas.slides import LecturePlan
from app.services.slides.generator import (
    enqueue_generation_job,
    get_job_status,
    get_deck,
)
from app.services.slides.theme_tokens import get_theme
from app.services.slides.pptx_builder import build_pptx
from app.services.slides.pdf_builder import build_pdf
from app.services.slides.thumbnail import render_cover_thumbnail
from app.clients.r2 import get_r2_client

logger = logging.getLogger(__name__)
router = APIRouter()


# ===========================
# RESPONSE MODELS
# ===========================

class ExportResponse(BaseModel):
    """Response model for export endpoints."""
    deck_id: str
    format: Literal["pptx", "pdf"]
    topic: str
    theme: Literal["minimalist", "chalkboard", "corporate"]
    slide_count: int
    download_url: str
    thumbnail_url: Optional[str] = None


# ===========================
# EXISTING ENDPOINTS
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


# ===========================
# EXPORT ENDPOINTS
# ===========================

@router.post("/export", response_model=ExportResponse)
async def export_pptx(
    plan: LecturePlan,
    user: CurrentUser = Depends(get_current_user),
) -> ExportResponse:
    """
    Export lecture plan to PPTX with cover thumbnail.
    
    Builds a PowerPoint presentation from the lecture plan, uploads to R2,
    and returns presigned download URLs.
    
    Args:
        plan: Lecture plan with slides and metadata
        user: Authenticated user
        
    Returns:
        Export metadata with download URLs
        
    Raises:
        HTTPException: If export or upload fails
    """
    error_id = str(uuid.uuid4())[:8]
    
    try:
        # Generate unique deck ID
        deck_id = str(uuid.uuid4())
        
        # Get theme configuration
        theme = get_theme(plan.theme)
        
        # Build PPTX
        logger.info(f"Building PPTX for deck {deck_id}: {plan.topic}")
        pptx_bytes = build_pptx(plan, theme)
        
        # Build cover thumbnail
        logger.info(f"Rendering cover thumbnail for deck {deck_id}")
        thumb_bytes = render_cover_thumbnail(plan.topic, theme)
        
        # Upload to R2
        r2_client = get_r2_client()
        
        pptx_key = f"decks/{deck_id}/deck.pptx"
        thumb_key = f"decks/{deck_id}/cover.png"
        
        logger.info(f"Uploading PPTX to R2: {pptx_key}")
        r2_client.put_object(
            pptx_key,
            pptx_bytes,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            metadata={"topic": plan.topic, "theme": plan.theme},
        )
        
        logger.info(f"Uploading thumbnail to R2: {thumb_key}")
        r2_client.put_object(
            thumb_key,
            thumb_bytes,
            "image/png",
            metadata={"topic": plan.topic},
        )
        
        # Generate presigned URLs (15 minutes expiry)
        download_url = r2_client.generate_presigned_url(pptx_key, expires_in=900)
        thumbnail_url = r2_client.generate_presigned_url(thumb_key, expires_in=900)
        
        logger.info(f"PPTX export complete for deck {deck_id}")
        
        return ExportResponse(
            deck_id=deck_id,
            format="pptx",
            topic=plan.topic,
            theme=plan.theme,
            slide_count=len(plan.slides) + 1,  # +1 for title slide
            download_url=download_url,
            thumbnail_url=thumbnail_url,
        )
        
    except ValueError as e:
        # Configuration or validation errors
        logger.error(f"[{error_id}] Export validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export validation failed: {str(e)} (error_id: {error_id})",
        )
    
    except RuntimeError as e:
        # R2 upload/URL generation errors
        logger.error(f"[{error_id}] R2 operation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage operation failed (error_id: {error_id})",
        )
    
    except Exception as e:
        # Unexpected errors
        logger.exception(f"[{error_id}] Unexpected error during PPTX export: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export PPTX (error_id: {error_id})",
        )


@router.post("/export-pdf", response_model=ExportResponse)
async def export_pdf_notes(
    plan: LecturePlan,
    user: CurrentUser = Depends(get_current_user),
) -> ExportResponse:
    """
    Export lecture plan to PDF with cheat-sheet and lecture notes.
    
    Builds a PDF with mindmap, flowchart, and detailed notes, uploads to R2,
    and returns presigned download URL.
    
    Args:
        plan: Lecture plan with slides and metadata
        user: Authenticated user
        
    Returns:
        Export metadata with download URL
        
    Raises:
        HTTPException: If export or upload fails
    """
    error_id = str(uuid.uuid4())[:8]
    
    try:
        # Generate unique deck ID
        deck_id = str(uuid.uuid4())
        
        # Get theme configuration
        theme = get_theme(plan.theme)
        
        # Build PDF
        logger.info(f"Building PDF for deck {deck_id}: {plan.topic}")
        pdf_bytes = build_pdf(plan, theme)
        
        # Upload to R2
        r2_client = get_r2_client()
        
        pdf_key = f"decks/{deck_id}/notes.pdf"
        
        logger.info(f"Uploading PDF to R2: {pdf_key}")
        r2_client.put_object(
            pdf_key,
            pdf_bytes,
            "application/pdf",
            metadata={
                "topic": plan.topic,
                "theme": plan.theme,
                "page_count": str(len(plan.slides) + 2),
            },
        )
        
        # Generate presigned URL (15 minutes expiry)
        download_url = r2_client.generate_presigned_url(pdf_key, expires_in=900)
        
        logger.info(f"PDF export complete for deck {deck_id}")
        
        return ExportResponse(
            deck_id=deck_id,
            format="pdf",
            topic=plan.topic,
            theme=plan.theme,
            slide_count=len(plan.slides) + 2,  # +2 for cheat-sheet pages
            download_url=download_url,
            thumbnail_url=None,  # No thumbnail for PDF
        )
        
    except ValueError as e:
        # Configuration or validation errors
        logger.error(f"[{error_id}] PDF export validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PDF export validation failed: {str(e)} (error_id: {error_id})",
        )
    
    except RuntimeError as e:
        # R2 upload/URL generation errors
        logger.error(f"[{error_id}] R2 operation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage operation failed (error_id: {error_id})",
        )
    
    except Exception as e:
        # Unexpected errors
        logger.exception(f"[{error_id}] Unexpected error during PDF export: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export PDF (error_id: {error_id})",
        )


@router.get("/themes", response_model=List[str])
async def list_themes() -> List[str]:
    """
    Get available presentation themes.
    
    Returns:
        List of theme identifiers
    """
    return ["minimalist", "chalkboard", "corporate"]