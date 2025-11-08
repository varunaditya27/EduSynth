from __future__ import annotations

import io
import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

# auth dep (adjust path if your project uses a different module)
try:
    from app.deps.auth import get_current_user, CurrentUser  # your existing dependency
except Exception:
    # Dev fallback if your auth dep differs; replace with your real one
    class CurrentUser(BaseModel):
        user_id: Optional[str] = None
        email: Optional[str] = None
    def get_current_user():  # type: ignore
        return CurrentUser(user_id=None, email=None)

# slide schemas (aligns with your existing LecturePlan)
try:
    from app.schemas.slides import LecturePlan
except Exception:
    # Minimal fallback to keep this file runnable if schema path differs.
    class SlideItem(BaseModel):
        title: str
        points: List[str] = []
        expanded_content: Optional[str] = None
        key_concepts: Optional[List[str]] = None
        supporting_details: Optional[List[str]] = None

    class LecturePlan(BaseModel):
        topic: str
        audience: Optional[str] = None
        duration_minutes: int = 15
        theme: str = "minimalist"
        preferred_format: str = "pptx"
        language: str = "en"
        slides: List[SlideItem] = []
        # optional orientation/device
        orientation: Optional[str] = "auto"
        device_preset: Optional[str] = None

from app.core.supabase_client import get_supabase_client

# your existing builders
from app.services.slides.pptx_builder import build_pptx
# enhanced pdf builder kept separate from classic pdf_builder to avoid conflicts
from app.services.slides.pdf_enhanced import build_enhanced_pdf

router = APIRouter(prefix="/v1/slides", tags=["slides"])


# -----------------------------------------------------------------------------
# Models for responses
# -----------------------------------------------------------------------------
class ExportResponse(BaseModel):
    status: str
    download_url: str
    thumbnail_url: Optional[str] = None


# -----------------------------------------------------------------------------
# Supabase persistence helper
# -----------------------------------------------------------------------------
def _save_generation_to_supabase(
    *, user_id: Optional[str], job_id: str, plan: LecturePlan,
    fmt: str, download_url: str, thumbnail_url: Optional[str] = None
):
    """
    Inserts a record into 'generated_assets' table.
    Non-blocking best-effort: if fails, we log and continue.
    """
    try:
        client = get_supabase_client()
        row = {
            "job_id": job_id,
            "user_id": user_id,
            "topic": plan.topic,
            "theme": plan.theme,
            "duration_minutes": plan.duration_minutes,
            "format": fmt,
            "r2_url": download_url,
            "thumbnail_url": thumbnail_url,
            "status": "completed",
        }
        client.table("generated_assets").insert(row).execute()
        logger.info(f"[supabase] saved asset row for job {job_id}")
    except Exception as e:
        logger.warning(f"[supabase] insert failed for {job_id}: {e}")


# -----------------------------------------------------------------------------
# PPTX Export
# -----------------------------------------------------------------------------
@router.post("/export", response_model=ExportResponse)
async def export_pptx(
    plan: LecturePlan,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Generates a PPTX in-memory, uploads it to your storage (R2 in your stack),
    and returns a public download URL. Here we return a placeholder URL since
    your R2 upload is elsewhere in your codebase.
    """
    try:
        pptx_bytes: bytes = build_pptx(plan, plan.theme)

        # TODO: integrate your real R2 upload here; keeping a simple deterministic key:
        key = f"decks/{uuid.uuid4().hex}_{plan.topic.replace(' ', '_')}.pptx"
        # Example public URL after upload (replace with your real builder/uploader output):
        download_url = f"https://r2.edusynth.com/{key}"
        # Optional thumbnail if your pipeline produced one
        thumbnail_url = f"https://r2.edusynth.com/{key.replace('.pptx', '_thumb.png')}"

        _save_generation_to_supabase(
            user_id=getattr(user, "user_id", None),
            job_id=key,
            plan=plan,
            fmt="pptx",
            download_url=download_url,
            thumbnail_url=thumbnail_url,
        )

        return ExportResponse(status="success", download_url=download_url, thumbnail_url=thumbnail_url)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PPTX export failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to export PPTX")


# -----------------------------------------------------------------------------
# PDF Export (Enhanced, with expanded content support)
# -----------------------------------------------------------------------------
@router.post("/export-pdf", response_model=ExportResponse)
async def export_pdf_notes(
    plan: LecturePlan,
    include_expanded_content: bool = False,  # kept for compatibility with your flow
    user: CurrentUser = Depends(get_current_user),
):
    """
    Generates an enhanced PDF (portrait/landscape auto), uploads to R2 (in your code),
    saves a Supabase row, and returns the URL.
    """
    try:
        pdf_bytes: bytes = build_enhanced_pdf(plan, plan.theme)

        # TODO: integrate your real R2 upload here
        key = f"notes/{uuid.uuid4().hex}_{plan.topic.replace(' ', '_')}.pdf"
        download_url = f"https://r2.edusynth.com/{key}"

        _save_generation_to_supabase(
            user_id=getattr(user, "user_id", None),
            job_id=key,
            plan=plan,
            fmt="pdf",
            download_url=download_url,
        )

        return ExportResponse(status="success", download_url=download_url)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF export failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to export PDF")


# -----------------------------------------------------------------------------
# History (recent assets for user or global if user_id absent)
# -----------------------------------------------------------------------------
@router.get("/history")
async def list_generation_history(
    user: CurrentUser = Depends(get_current_user),
):
    """
    Returns recent generated assets; if you have real user IDs in tokens,
    this filters by the current user; else returns global feed.
    """
    try:
        client = get_supabase_client()
        query = client.table("generated_assets").select("*").order("created_at", desc=True)
        if getattr(user, "user_id", None):
            query = query.eq("user_id", user.user_id)
        res = query.limit(50).execute()
        return res.data or []
    except Exception as e:
        logger.error(f"Failed to fetch history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch history")
