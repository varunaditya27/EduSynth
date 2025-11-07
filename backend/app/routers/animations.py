# backend/app/routers/animations.py
"""
API endpoints for interactive animation generation and retrieval.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional

from app.models.animations import (
    AnimationGenerationRequest,
    LectureAnimations
)
from app.animation_generator import generate_animations, load_animations


router = APIRouter()


@router.post("/generate", response_model=dict)
async def generate_lecture_animations(
    request: AnimationGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate interactive animation metadata for a lecture.
    
    This creates step-by-step animated sequences with interactive elements
    that transform passive viewing into active learning.
    
    Returns:
        Dictionary with task_id and status
    """
    try:
        # Parse length string to minutes
        length_str = request.length.lower().replace("minutes", "").replace("minute", "").replace("min", "").strip()
        try:
            minutes = max(1, int(float(length_str)))
        except:
            minutes = 5
        
        # Generate animations synchronously for now (can be moved to background)
        task_id, animations = generate_animations(
            topic=request.topic,
            audience=request.audience,
            minutes=minutes,
            theme=request.theme,
            interaction_level=request.interaction_level,
            animation_style=request.animation_style
        )
        
        return {
            "task_id": task_id,
            "status": "completed",
            "message": f"Generated {len(animations.slides)} interactive slides with {animations.interaction_count} interactions",
            "estimated_time_seconds": animations.total_estimated_time_seconds,
            "interaction_count": animations.interaction_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Animation generation failed: {str(e)}")


@router.get("/{task_id}", response_model=LectureAnimations)
async def get_animations(task_id: str):
    """
    Retrieve animation metadata for a specific lecture.
    
    Args:
        task_id: The unique identifier for the lecture
        
    Returns:
        Complete animation data including all slides, steps, and interactions
    """
    try:
        animations = load_animations(task_id)
        return animations
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Animations not found for task {task_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load animations: {str(e)}")


@router.get("/{task_id}/slides/{slide_index}", response_model=dict)
async def get_slide_animation(task_id: str, slide_index: int):
    """
    Get animation data for a specific slide.
    
    Args:
        task_id: The lecture identifier
        slide_index: Index of the slide (0-based)
        
    Returns:
        Animation data for the specified slide
    """
    try:
        animations = load_animations(task_id)
        
        if slide_index < 0 or slide_index >= len(animations.slides):
            raise HTTPException(
                status_code=404,
                detail=f"Slide {slide_index} not found (total slides: {len(animations.slides)})"
            )
        
        slide = animations.slides[slide_index]
        return {
            "slide": slide.model_dump(),
            "total_slides": len(animations.slides),
            "current_index": slide_index
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Animations not found for task {task_id}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load slide: {str(e)}")


@router.get("/{task_id}/metadata", response_model=dict)
async def get_animation_metadata(task_id: str):
    """
    Get high-level metadata about the lecture animations.
    
    Args:
        task_id: The lecture identifier
        
    Returns:
        Summary metadata (topic, slide count, interaction count, etc.)
    """
    try:
        animations = load_animations(task_id)
        
        return {
            "task_id": animations.lecture_id,
            "topic": animations.topic,
            "audience": animations.audience,
            "theme": animations.theme,
            "slide_count": len(animations.slides),
            "interaction_count": animations.interaction_count,
            "estimated_time_seconds": animations.total_estimated_time_seconds,
            "gamification": animations.gamification,
            "slides_overview": [
                {
                    "index": i,
                    "title": slide.title,
                    "concept": slide.concept,
                    "steps": len(slide.steps),
                    "interactions": len(slide.interactions),
                    "difficulty": slide.difficulty
                }
                for i, slide in enumerate(animations.slides)
            ]
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Animations not found for task {task_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load metadata: {str(e)}")


@router.post("/{task_id}/progress", response_model=dict)
async def track_progress(task_id: str, completed_slides: list[int], score: Optional[int] = None):
    """
    Track learner progress through the animated lecture.
    
    Args:
        task_id: The lecture identifier
        completed_slides: List of slide indices the user has completed
        score: Optional score from quiz interactions
        
    Returns:
        Progress summary and recommendations
    """
    try:
        animations = load_animations(task_id)
        total_slides = len(animations.slides)
        completed_count = len(completed_slides)
        progress_percent = (completed_count / total_slides * 100) if total_slides > 0 else 0
        
        # Calculate potential points
        total_points = animations.gamification.get("total_points", 0) if animations.gamification else 0
        earned_points = score if score is not None else 0
        
        # Determine next recommended slide
        next_slide = None
        for i in range(total_slides):
            if i not in completed_slides:
                next_slide = i
                break
        
        return {
            "progress_percent": round(progress_percent, 1),
            "completed_slides": completed_count,
            "total_slides": total_slides,
            "remaining_slides": total_slides - completed_count,
            "estimated_time_remaining": sum(
                animations.slides[i].estimated_time_seconds
                for i in range(total_slides)
                if i not in completed_slides
            ),
            "points_earned": earned_points,
            "points_possible": total_points,
            "next_slide_index": next_slide,
            "completion_status": "completed" if completed_count == total_slides else "in_progress"
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Animations not found for task {task_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track progress: {str(e)}")
