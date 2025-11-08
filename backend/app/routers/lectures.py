"""
Lectures Router - CRUD operations for lectures
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel, field_serializer
from datetime import datetime
from prisma import Prisma
from prisma.enums import VideoStatus, VisualTheme
from app.db import get_client

router = APIRouter()

# Helper function to map VideoStatus enum to frontend format
def map_video_status(status) -> str:
    """Map VideoStatus enum to frontend-expected format"""
    status_map = {
        VideoStatus.PENDING: "pending",
        VideoStatus.GENERATING_CONTENT: "processing",
        VideoStatus.CREATING_SLIDES: "processing",
        VideoStatus.FETCHING_IMAGES: "processing",
        VideoStatus.GENERATING_AUDIO: "processing",
        VideoStatus.ASSEMBLING_VIDEO: "processing",
        VideoStatus.COMPLETED: "completed",
        VideoStatus.FAILED: "failed"
    }
    return status_map.get(status, "pending")

# Pydantic models for request/response
class CreateLectureRequest(BaseModel):
    topic: str
    targetAudience: Optional[str] = None
    desiredLength: int
    visualTheme: Optional[str] = "MINIMALIST"
    userId: Optional[str] = None  # Optional for system-generated lectures

class UpdateLectureRequest(BaseModel):
    videoUrl: Optional[str] = None
    slidesPdfUrl: Optional[str] = None
    videoStatus: Optional[str] = None
    animationTaskId: Optional[str] = None
    animationStatus: Optional[str] = None
    hasInteractive: Optional[bool] = None
    processingCompletedAt: Optional[datetime] = None
    errorMessage: Optional[str] = None

class LectureResponse(BaseModel):
    id: str
    topic: str
    targetAudience: Optional[str]
    desiredLength: int
    visualTheme: str
    videoUrl: Optional[str]
    slidesPdfUrl: Optional[str]
    videoStatus: str
    animationTaskId: Optional[str]
    animationStatus: Optional[str]
    hasInteractive: bool
    processingStartedAt: Optional[datetime]
    processingCompletedAt: Optional[datetime]
    errorMessage: Optional[str]
    userId: Optional[str]  # Optional for system-generated lectures
    createdAt: datetime
    updatedAt: datetime
    
    model_config = {"from_attributes": True}

@router.post("", response_model=LectureResponse)
async def create_lecture(request: CreateLectureRequest, db: Prisma = Depends(get_client)):
    """Create a new lecture"""
    try:
        lecture = await db.lecture.create(
            data={
                "topic": request.topic,
                "targetAudience": request.targetAudience,
                "desiredLength": request.desiredLength,
                "visualTheme": VisualTheme(request.visualTheme) if request.visualTheme else VisualTheme.MINIMALIST,
                "userId": request.userId,
                "videoStatus": VideoStatus.PENDING,
                "processingStartedAt": datetime.utcnow()
            }
        )
        return lecture
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create lecture: {str(e)}")

@router.get("", response_model=List[LectureResponse])
async def get_lectures(userId: Optional[str] = None, db: Prisma = Depends(get_client)):
    """Get all lectures, optionally filtered by userId"""
    try:
        where = {"userId": userId} if userId else {}
        lectures = await db.lecture.find_many(
            where=where,
            order={"createdAt": "desc"}
        )
        
        # Transform lectures to frontend format
        return [
            LectureResponse(
                id=lecture.id,
                topic=lecture.topic,
                targetAudience=lecture.targetAudience,
                desiredLength=lecture.desiredLength,
                visualTheme=str(lecture.visualTheme),
                videoUrl=lecture.videoUrl,
                slidesPdfUrl=lecture.slidesPdfUrl,
                videoStatus=map_video_status(lecture.videoStatus),
                animationTaskId=lecture.animationTaskId,
                animationStatus=map_video_status(lecture.animationStatus) if lecture.animationStatus else None,
                hasInteractive=lecture.hasInteractive,
                processingStartedAt=lecture.processingStartedAt,
                processingCompletedAt=lecture.processingCompletedAt,
                errorMessage=lecture.errorMessage,
                userId=lecture.userId,
                createdAt=lecture.createdAt,
                updatedAt=lecture.updatedAt
            )
            for lecture in lectures
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch lectures: {str(e)}")

@router.get("/{lecture_id}", response_model=LectureResponse)
async def get_lecture(lecture_id: str, db: Prisma = Depends(get_client)):
    """Get a specific lecture by ID"""
    try:
        lecture = await db.lecture.find_unique(where={"id": lecture_id})
        if not lecture:
            raise HTTPException(status_code=404, detail="Lecture not found")
        
        # Transform to frontend format
        return LectureResponse(
            id=lecture.id,
            topic=lecture.topic,
            targetAudience=lecture.targetAudience,
            desiredLength=lecture.desiredLength,
            visualTheme=str(lecture.visualTheme),
            videoUrl=lecture.videoUrl,
            slidesPdfUrl=lecture.slidesPdfUrl,
            videoStatus=map_video_status(lecture.videoStatus),
            animationTaskId=lecture.animationTaskId,
            animationStatus=map_video_status(lecture.animationStatus) if lecture.animationStatus else None,
            hasInteractive=lecture.hasInteractive,
            processingStartedAt=lecture.processingStartedAt,
            processingCompletedAt=lecture.processingCompletedAt,
            errorMessage=lecture.errorMessage,
            userId=lecture.userId,
            createdAt=lecture.createdAt,
            updatedAt=lecture.updatedAt
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch lecture: {str(e)}")

@router.patch("/{lecture_id}", response_model=LectureResponse)
async def update_lecture(lecture_id: str, request: UpdateLectureRequest, db: Prisma = Depends(get_client)):
    """Update a lecture"""
    try:
        # Check if lecture exists
        existing = await db.lecture.find_unique(where={"id": lecture_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Lecture not found")
        
        # Build update data (only include fields that were provided)
        update_data = {}
        if request.videoUrl is not None:
            update_data["videoUrl"] = request.videoUrl
        if request.slidesPdfUrl is not None:
            update_data["slidesPdfUrl"] = request.slidesPdfUrl
        if request.videoStatus is not None:
            update_data["videoStatus"] = VideoStatus(request.videoStatus)
        if request.animationTaskId is not None:
            update_data["animationTaskId"] = request.animationTaskId
        if request.animationStatus is not None:
            update_data["animationStatus"] = VideoStatus(request.animationStatus)
        if request.hasInteractive is not None:
            update_data["hasInteractive"] = request.hasInteractive
        if request.processingCompletedAt is not None:
            update_data["processingCompletedAt"] = request.processingCompletedAt
        if request.errorMessage is not None:
            update_data["errorMessage"] = request.errorMessage
        
        lecture = await db.lecture.update(
            where={"id": lecture_id},
            data=update_data
        )
        return lecture
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update lecture: {str(e)}")

@router.delete("/{lecture_id}")
async def delete_lecture(lecture_id: str, db: Prisma = Depends(get_client)):
    """Delete a lecture"""
    try:
        # Check if lecture exists
        existing = await db.lecture.find_unique(where={"id": lecture_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Lecture not found")
        
        await db.lecture.delete(where={"id": lecture_id})
        return {"message": "Lecture deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete lecture: {str(e)}")
