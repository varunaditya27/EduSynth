"""
Mindmap API Router - Endpoints for mindmap generation and management.
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from prisma import Prisma

from app.deps.auth import get_current_user
from app.db import get_client
from app.models.mindmap import (
    MindMapGenerateRequest,
    MindMapResponse,
    MindMapRetrieveResponse,
    MindMapDeleteResponse,
    MindMapHealthResponse,
    MindMapError
)
from app.services.mindmap import mindmap_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mindmap", tags=["mindmap"])


@router.post(
    "/generate",
    response_model=MindMapResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate mindmap for a lecture",
    description="Generate a comprehensive mindmap for a lecture using Gemini 2.5 Pro. "
                "Requires JWT authentication. Returns hierarchical mindmap structure and Mermaid syntax."
)
async def generate_mindmap(
    request: MindMapGenerateRequest,
    current_user: dict = Depends(get_current_user),
    db: Prisma = Depends(get_client)
):
    """
    Generate a mindmap for a lecture.
    
    - **lecture_id**: ID of the lecture to generate mindmap for
    - **regenerate**: Force regeneration if mindmap already exists (default: False)
    - **max_branches**: Maximum number of main branches (3-10, default: 6)
    - **max_depth**: Maximum depth of hierarchy (2-5, default: 3)
    
    Returns the generated mindmap with hierarchical structure and Mermaid diagram syntax.
    """
    try:
        # Check if lecture exists and belongs to user
        lecture = await db.lecture.find_unique(
            where={"id": request.lecture_id},
            include={"mindMap": True}
        )
        
        if not lecture:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lecture {request.lecture_id} not found"
            )
        
        if lecture.userId != current_user["sub"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to generate mindmap for this lecture"
            )
        
        # Check if mindmap already exists
        if lecture.mindMap and not request.regenerate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Mindmap already exists for this lecture. Set regenerate=true to recreate."
            )
        
        # Generate mindmap using Gemini
        logger.info(f"Generating mindmap for lecture {request.lecture_id}")
        
        result = await mindmap_service.generate_mindmap(
            lecture_topic=lecture.topic,
            lecture_audience=lecture.targetAudience or "General audience",
            lecture_duration=lecture.desiredLength,
            max_branches=request.max_branches,
            max_depth=request.max_depth
        )
        
        # Convert MindMapData to dict for JSON storage
        mindmap_dict = result["mindmap_data"].model_dump(by_alias=True)
        
        # Save or update in database
        if lecture.mindMap:
            # Update existing mindmap
            mindmap = await db.mindmap.update(
                where={"lectureId": request.lecture_id},
                data={
                    "data": mindmap_dict,
                    "mermaidSyntax": result["mermaid_syntax"],
                    "nodeCount": result["metadata"]["node_count"],
                    "branchCount": result["metadata"]["branch_count"],
                    "maxDepth": result["metadata"]["max_depth"],
                    "updatedAt": datetime.utcnow()
                }
            )
            logger.info(f"Updated mindmap {mindmap.id} for lecture {request.lecture_id}")
        else:
            # Create new mindmap
            mindmap = await db.mindmap.create(
                data={
                    "lectureId": request.lecture_id,
                    "data": mindmap_dict,
                    "mermaidSyntax": result["mermaid_syntax"],
                    "nodeCount": result["metadata"]["node_count"],
                    "branchCount": result["metadata"]["branch_count"],
                    "maxDepth": result["metadata"]["max_depth"]
                }
            )
            logger.info(f"Created mindmap {mindmap.id} for lecture {request.lecture_id}")
        
        # Return response
        return MindMapResponse(
            lecture_id=request.lecture_id,
            mindmap_id=mindmap.id,
            mind_map=result["mindmap_data"],
            mermaid_syntax=result["mermaid_syntax"],
            metadata=result["metadata"],
            created_at=mindmap.createdAt
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error generating mindmap: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating mindmap: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate mindmap: {str(e)}"
        )


@router.get(
    "/lecture/{lecture_id}",
    response_model=MindMapRetrieveResponse,
    summary="Get mindmap for a lecture",
    description="Retrieve an existing mindmap for a lecture. Requires JWT authentication."
)
async def get_mindmap_by_lecture(
    lecture_id: str,
    current_user: dict = Depends(get_current_user),
    db: Prisma = Depends(get_client)
):
    """
    Retrieve the mindmap for a specific lecture.
    
    - **lecture_id**: ID of the lecture
    
    Returns the mindmap with all details if it exists.
    """
    try:
        # Check if lecture exists and belongs to user
        lecture = await db.lecture.find_unique(
            where={"id": lecture_id},
            include={"mindMap": True}
        )
        
        if not lecture:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lecture {lecture_id} not found"
            )
        
        if lecture.userId != current_user["sub"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this mindmap"
            )
        
        if not lecture.mindMap:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No mindmap found for lecture {lecture_id}"
            )
        
        mindmap = lecture.mindMap
        
        # Parse mindmap data from JSON
        from app.models.mindmap import MindMapData
        mindmap_data = MindMapData.model_validate(mindmap.data)
        
        # Calculate metadata
        metadata = {
            "node_count": mindmap.nodeCount,
            "branch_count": mindmap.branchCount,
            "max_depth": mindmap.maxDepth,
            "connection_count": len(mindmap_data.connections)
        }
        
        return MindMapRetrieveResponse(
            lecture_id=lecture_id,
            mindmap_id=mindmap.id,
            mind_map=mindmap_data,
            mermaid_syntax=mindmap.mermaidSyntax,
            metadata=metadata,
            created_at=mindmap.createdAt,
            updated_at=mindmap.updatedAt
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving mindmap: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve mindmap: {str(e)}"
        )


@router.get(
    "/{mindmap_id}",
    response_model=MindMapRetrieveResponse,
    summary="Get mindmap by ID",
    description="Retrieve a mindmap by its ID. Requires JWT authentication."
)
async def get_mindmap_by_id(
    mindmap_id: str,
    current_user: dict = Depends(get_current_user),
    db: Prisma = Depends(get_client)
):
    """
    Retrieve a mindmap by its unique ID.
    
    - **mindmap_id**: ID of the mindmap
    
    Returns the mindmap with all details if it exists.
    """
    try:
        mindmap = await db.mindmap.find_unique(
            where={"id": mindmap_id},
            include={"lecture": True}
        )
        
        if not mindmap:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mindmap {mindmap_id} not found"
            )
        
        if mindmap.lecture.userId != current_user["sub"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this mindmap"
            )
        
        # Parse mindmap data from JSON
        from app.models.mindmap import MindMapData
        mindmap_data = MindMapData.model_validate(mindmap.data)
        
        # Calculate metadata
        metadata = {
            "node_count": mindmap.nodeCount,
            "branch_count": mindmap.branchCount,
            "max_depth": mindmap.maxDepth,
            "connection_count": len(mindmap_data.connections)
        }
        
        return MindMapRetrieveResponse(
            lecture_id=mindmap.lectureId,
            mindmap_id=mindmap.id,
            mind_map=mindmap_data,
            mermaid_syntax=mindmap.mermaidSyntax,
            metadata=metadata,
            created_at=mindmap.createdAt,
            updated_at=mindmap.updatedAt
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving mindmap: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve mindmap: {str(e)}"
        )


@router.delete(
    "/lecture/{lecture_id}",
    response_model=MindMapDeleteResponse,
    summary="Delete mindmap for a lecture",
    description="Delete the mindmap associated with a lecture. Requires JWT authentication."
)
async def delete_mindmap(
    lecture_id: str,
    current_user: dict = Depends(get_current_user),
    db: Prisma = Depends(get_client)
):
    """
    Delete a mindmap for a specific lecture.
    
    - **lecture_id**: ID of the lecture
    
    Returns confirmation of deletion.
    """
    try:
        # Check if lecture exists and belongs to user
        lecture = await db.lecture.find_unique(
            where={"id": lecture_id},
            include={"mindMap": True}
        )
        
        if not lecture:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lecture {lecture_id} not found"
            )
        
        if lecture.userId != current_user["sub"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this mindmap"
            )
        
        if not lecture.mindMap:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No mindmap found for lecture {lecture_id}"
            )
        
        # Delete mindmap
        await db.mindmap.delete(
            where={"lectureId": lecture_id}
        )
        
        logger.info(f"Deleted mindmap for lecture {lecture_id}")
        
        return MindMapDeleteResponse(
            message="Mindmap deleted successfully",
            lecture_id=lecture_id,
            deleted_at=datetime.utcnow()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting mindmap: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete mindmap: {str(e)}"
        )


@router.get(
    "/health",
    response_model=MindMapHealthResponse,
    summary="Health check",
    description="Check if the mindmap service is operational. No authentication required."
)
async def health_check(db: Prisma = Depends(get_client)):
    """
    Check the health status of the mindmap service.
    
    Returns service status, Gemini availability, and database connectivity.
    """
    try:
        # Check Gemini API
        gemini_available = bool(mindmap_service.model)
        
        # Check database
        try:
            await db.execute_raw("SELECT 1")
            database_connected = True
        except:
            database_connected = False
        
        return MindMapHealthResponse(
            status="healthy" if (gemini_available and database_connected) else "degraded",
            service="mindmap",
            gemini_available=gemini_available,
            database_connected=database_connected
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return MindMapHealthResponse(
            status="unhealthy",
            service="mindmap",
            gemini_available=False,
            database_connected=False
        )
