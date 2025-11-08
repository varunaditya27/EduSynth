"""
PDF Generation Router - Generates PDFs from lecture plans during video creation
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from pathlib import Path
from typing import Optional, List, Literal
import json
import uuid
import boto3
from botocore.client import Config as BotoConfig

from app.core.config import settings
from app.schemas.slides import LecturePlan, SlideItem
from app.services.slides.pdf_builder import build_pdf
from app.services.slides.theme_tokens import get_theme
from app.gemini_generator import generate_slides

router = APIRouter(prefix="/v1/pdf", tags=["pdf"])

OUTDIR = Path(__file__).resolve().parent.parent.parent / "output"
OUTDIR.mkdir(parents=True, exist_ok=True)


class PDFGenerationRequest(BaseModel):
    topic: str
    audience: str
    length: str
    theme: Optional[str] = "minimalist"
    orientation: Optional[Literal["auto", "portrait", "landscape"]] = "auto"
    device_preset: Optional[Literal["desktop", "tablet", "mobile"]] = None
    cheatsheet_only: bool = False
    notes_only: bool = False


class PDFGenerationResponse(BaseModel):
    task_id: str
    status: str
    message: str
    pdf_url: Optional[str] = None


def _parse_minutes(length: str) -> int:
    """Convert string like '10 min' → int."""
    if isinstance(length, int):
        return length
    if not length:
        return 5
    s = str(length).lower().replace("minutes", "").replace("minute", "").replace("min", "").strip()
    try:
        return max(1, int(float(s)))
    except Exception:
        return 5


def _upload_pdf_to_r2(local_path: Path, s3_key: str) -> str:
    """Upload PDF to Cloudflare R2."""
    endpoint = settings.CLOUDFLARE_S3_ENDPOINT
    bucket = settings.CLOUDFLARE_S3_BUCKET_NAME
    access_key = settings.CLOUDFLARE_S3_ACCESS_KEY_ID
    secret_key = settings.CLOUDFLARE_S3_SECRET_ACCESS_KEY
    public_url = settings.CLOUDFLARE_R2_PUBLIC_URL

    if not all([endpoint, bucket, access_key, secret_key]):
        raise RuntimeError("Missing Cloudflare R2 configuration. Check .env.")
    
    if not public_url:
        raise RuntimeError("Missing CLOUDFLARE_R2_PUBLIC_URL in .env.")

    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=BotoConfig(signature_version="s3v4"),
    )

    # Upload PDF with public-read ACL
    s3.upload_file(
        str(local_path), 
        bucket, 
        s3_key,
        ExtraArgs={'ACL': 'public-read', 'ContentType': 'application/pdf'}
    )

    return f"{public_url.rstrip('/')}/{s3_key}"


@router.post("/generate", response_model=PDFGenerationResponse)
async def generate_pdf(req: PDFGenerationRequest, background_tasks: BackgroundTasks):
    """
    Generate PDF from lecture plan with theme and adaptive layout.
    """
    task_id = str(uuid.uuid4())
    minutes = _parse_minutes(req.length)

    try:
        # Generate slides using Gemini
        theme_key = (req.theme or "minimalist").lower()
        _, slide_list = generate_slides(req.topic, req.audience, minutes, theme_key)
        
        # Build LecturePlan
        slides = [
            SlideItem(
                index=s.get("index", i),
                title=s.get("title", ""),
                points=s.get("points", []),
                diagram=s.get("diagram"),
            )
            for i, s in enumerate(slide_list)
        ]
        
        plan = LecturePlan(
            topic=req.topic,
            theme=theme_key,
            duration_minutes=minutes,
            slides=slides,
            orientation=req.orientation,
            device_preset=req.device_preset,
        )
        
        # Get theme tokens
        theme = get_theme(theme_key)
        
        # Generate PDF
        pdf_bytes = build_pdf(
            plan=plan,
            theme=theme,
            cheatsheet_only=req.cheatsheet_only,
            notes_only=req.notes_only,
        )
        
        # Save PDF locally
        pdf_dir = OUTDIR / task_id
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = pdf_dir / f"{task_id}.pdf"
        pdf_path.write_bytes(pdf_bytes)
        
        # Upload to R2
        s3_key = f"edusynth/{task_id}/{task_id}.pdf"
        pdf_url = _upload_pdf_to_r2(pdf_path, s3_key)
        
        # Save metadata
        meta_path = pdf_dir / "meta.json"
        meta_path.write_text(
            json.dumps({
                "task_id": task_id,
                "topic": req.topic,
                "theme": theme_key,
                "pdf_url": pdf_url,
            }, indent=2),
            encoding="utf-8"
        )
        
        return PDFGenerationResponse(
            task_id=task_id,
            status="completed",
            message="PDF generated successfully",
            pdf_url=pdf_url,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/status/{task_id}")
async def get_pdf_status(task_id: str):
    """
    Get the status of PDF generation.
    """
    try:
        meta_file = OUTDIR / task_id / "meta.json"
        if not meta_file.exists():
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
        
        return {
            "task_id": task_id,
            "status": "completed",
            "pdf_url": meta_data.get("pdf_url"),
            "topic": meta_data.get("topic"),
            "theme": meta_data.get("theme"),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")
