"""
Slide Deck API routes with enhanced PPTX and PDF export.
Supports adaptive layouts, device presets, orientation settings, and dual content generation.
"""

import logging
import os
import uuid
from typing import List, Literal, Optional

import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.slides.dual_content import DualContentGenerator

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
    # Adaptive layout metadata
    orientation: Optional[str] = None
    device_preset: Optional[str] = None


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

    If the incoming model supports expanded-generation flags, we honor them.
    Otherwise we skip gracefully (no AttributeError).
    """
    # Expanded content flags (guarded)
    want_expanded = getattr(request, "generate_expanded_content", False)
    expanded_level = getattr(request, "expanded_content_level", "detailed")

    # If expanded content is requested, configure Gemini and enrich slides
    if want_expanded:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY is missing in environment."
            )
        genai.configure(api_key=api_key)
        # Use a current model; keep in sync with your other generators
        model = genai.GenerativeModel("gemini-1.5-pro")
        dual_generator = DualContentGenerator(model=model, level=expanded_level)

        # Some request models may or may not include 'slides'.
        # If slides exist, enrich them. Otherwise the downstream
        # queue worker will generate content from topic/audience.
        if hasattr(request, "slides") and request.slides:
            for slide in request.slides:
                # 'slide' may be a BaseModel or dict; normalize access
                title = getattr(slide, "title", None) or slide.get("title")
                points = getattr(slide, "points", None) or slide.get("points") or []
                # Only force refresh if explicitly requested or content missing
                force_refresh = getattr(request, "force_refresh_content", False)
                expanded = await dual_generator.generate_dual_content(
                    topic=request.topic,
                    force_refresh=force_refresh,
                    title=title,
                    points=points,
                )
                # write back safely (supports BaseModel or dict)
                if hasattr(slide, "__setattr__"):
                    setattr(slide, "expanded_content", expanded["expanded_content"])
                    setattr(slide, "key_concepts", expanded["key_concepts"])
                    setattr(slide, "supporting_details", expanded["supporting_details"])
                else:
                    slide["expanded_content"] = expanded["expanded_content"]
                    slide["key_concepts"] = expanded["key_concepts"]
                    slide["supporting_details"] = expanded["supporting_details"]

    # Queue generation job with whatever we’ve got
    job_id = await enqueue_generation_job(user.user_id, request)
    return JobQueuedResponse(job_id=job_id, status="QUEUED")


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(
    job_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> JobStatusResponse:
    status_data = await get_job_status(user.user_id, job_id)
    return JobStatusResponse(**status_data)


@router.get("/{deck_id}", response_model=DeckResponse)
async def get_deck_info(
    deck_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> DeckResponse:
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
    error_id = str(uuid.uuid4())[:8]

    try:
        deck_id = str(uuid.uuid4())
        theme = get_theme(plan.theme)

        logger.info(
            f"Building PPTX for deck {deck_id}: {plan.topic} "
            f"(preset={plan.device_preset}, orientation={plan.orientation})"
        )
        pptx_bytes = build_pptx(plan, theme)

        # Cover thumbnail
        thumb_bytes = render_cover_thumbnail(plan.topic, theme, size=(1280, 720))

        # Upload to R2
        r2_client = get_r2_client()
        pptx_key = f"decks/{deck_id}/deck.pptx"
        thumb_key = f"decks/{deck_id}/cover.png"

        r2_client.put_object(
            pptx_key,
            pptx_bytes,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            metadata={
                "topic": plan.topic,
                "orientation": plan.orientation or "auto",
                "device_preset": plan.device_preset or "desktop",
            },
        )
        r2_client.put_object(
            thumb_key,
            thumb_bytes,
            "image/png",
            metadata={"topic": plan.topic},
        )

        download_url = r2_client.generate_presigned_url(pptx_key, expires_in=900)
        thumbnail_url = r2_client.generate_presigned_url(thumb_key, expires_in=900)

        return ExportResponse(
            deck_id=deck_id,
            format="pptx",
            topic=plan.topic,
            theme=plan.theme,
            slide_count=len(plan.slides) + 1,  # +1 for title slide
            download_url=download_url,
            thumbnail_url=thumbnail_url,
            orientation=plan.orientation,
            device_preset=plan.device_preset,
        )

    except ValueError as e:
        logger.error(f"[{error_id}] Export validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export validation failed: {str(e)} (error_id: {error_id})",
        )

    except RuntimeError as e:
        logger.error(f"[{error_id}] R2 operation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage operation failed (error_id: {error_id})",
        )

    except Exception as e:
        logger.exception(f"[{error_id}] Unexpected error during export: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export document (error_id: {error_id})",
        )


@router.post("/export-pdf", response_model=ExportResponse)
async def export_pdf_notes(
    plan: LecturePlan,
    user: CurrentUser = Depends(get_current_user),
    include_expanded_content: bool = False
) -> ExportResponse:
    error_id = str(uuid.uuid4())[:8]

    try:
        deck_id = str(uuid.uuid4())
        theme = get_theme(plan.theme)

        want_expanded = include_expanded_content
        logger.info(
            f"Building PDF for deck {deck_id}: {plan.topic} "
            f"(preset={plan.device_preset}, orientation={plan.orientation}, "
            f"expanded={want_expanded})"
        )

        # Only generate if missing or empty (not just attribute exists)
        if want_expanded:
            missing = any(
                not getattr(s, "expanded_content", None) for s in plan.slides
            )
            if missing:
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise HTTPException(
                        status_code=500,
                        detail="GEMINI_API_KEY is missing in environment."
                    )
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-pro")
                level = getattr(plan, "expanded_content_level", "detailed")
                dual_generator = DualContentGenerator(model=model, level=level)

                for slide in plan.slides:
                    if not getattr(slide, "expanded_content", None):
                        expanded = await dual_generator.generate_dual_content(
                            topic=plan.topic,
                            title=slide.title,
                            points=slide.points,
                        )
                        slide.expanded_content = expanded["expanded_content"]
                        slide.key_concepts = expanded["key_concepts"]
                        slide.supporting_details = expanded["supporting_details"]

        # Build PDF
        if want_expanded:
            from app.services.slides.pdf_enhanced import build_enhanced_pdf
            pdf_bytes = build_enhanced_pdf(plan, theme)
        else:
            pdf_bytes = build_pdf(plan, theme)

        # Upload to R2
        r2_client = get_r2_client()
        pdf_key = f"decks/{deck_id}/notes.pdf"

        r2_client.put_object(
            pdf_key,
            pdf_bytes,
            "application/pdf",
            metadata={
                "topic": plan.topic,
                "page_count": str(len(plan.slides) + 2),
                "orientation": plan.orientation or "auto",
                "device_preset": plan.device_preset or "desktop",
            },
        )

        download_url = r2_client.generate_presigned_url(pdf_key, expires_in=900)

        return ExportResponse(
            deck_id=deck_id,
            format="pdf",
            topic=plan.topic,
            theme=plan.theme,
            slide_count=len(plan.slides) + 2,  # +2 for splash + flow
            download_url=download_url,
            thumbnail_url=None,
            orientation=plan.orientation,
            device_preset=plan.device_preset,
        )

    except ValueError as e:
        logger.error(f"[{error_id}] PDF export validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PDF export validation failed: {str(e)} (error_id: {error_id})",
        )
    except RuntimeError as e:
        logger.error(f"[{error_id}] R2 operation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage operation failed (error_id: {error_id})",
        )
    except Exception as e:
        logger.exception(f"[{error_id}] Unexpected error during PDF export: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export PDF (error_id: {error_id})",
        )


@router.get("/themes", response_model=List[str])
async def list_themes() -> List[str]:
    return ["minimalist", "chalkboard", "corporate"]


@router.get("/presets", response_model=List[dict])
async def list_device_presets() -> List[dict]:
    return [
        {
            "id": "desktop",
            "name": "Desktop (16:9)",
            "aspect_ratio": "16:9",
            "dimensions": '13.33" × 7.5"',
            "recommended_for": "Presentations, online meetings",
        },
        {
            "id": "tablet",
            "name": "Tablet (4:3)",
            "aspect_ratio": "4:3",
            "dimensions": '10" × 7.5"',
            "recommended_for": "Classic projectors, iPads",
        },
        {
            "id": "mobile",
            "name": "Mobile (9:16)",
            "aspect_ratio": "9:16",
            "dimensions": '7.5" × 13.33"',
            "recommended_for": "Phone viewing, stories",
        },
    ]
