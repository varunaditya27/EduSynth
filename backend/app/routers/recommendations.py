# backend/app/routers/recommendations.py

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional, Literal, List

from app.models.recommendations import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendationError
)
from app.services.recommendations import recommendation_service
from app.deps.auth import get_current_user, CurrentUser


router = APIRouter()


@router.post(
    "/generate",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Learning Resource Recommendations",
    description="""
    Generate personalized learning resource recommendations for a given topic using Gemini 2.5 Pro with Google Search grounding.
    
    This endpoint uses Google Search to find REAL, VERIFIED resources (blogs, YouTube videos, websites, courses, documentation)
    and ensures that all URLs are actual, accessible links that exist on the internet.
    
    Features:
    - Uses Gemini 2.5 Pro with Google Search grounding to prevent hallucination
    - Returns only verified, real URLs from actual search results
    - Supports filtering by resource type and audience level
    - Provides relevance scores for each recommendation
    - Includes author/source information when available
    
    Authentication: Required (JWT token)
    """,
    responses={
        200: {
            "description": "Successfully generated recommendations",
            "model": RecommendationResponse
        },
        401: {
            "description": "Unauthorized - Invalid or missing authentication token"
        },
        422: {
            "description": "Validation Error - Invalid request parameters"
        },
        500: {
            "description": "Internal Server Error - Failed to generate recommendations",
            "model": RecommendationError
        }
    }
)
async def generate_recommendations(
    request: RecommendationRequest,
    current_user: CurrentUser = Depends(get_current_user)
) -> RecommendationResponse:
    """
    Generate learning resource recommendations for a topic.
    
    Args:
        request: Recommendation request with topic, resource types, and preferences
        current_user: Authenticated user from JWT token
        
    Returns:
        RecommendationResponse with verified, grounded recommendations
        
    Raises:
        HTTPException: 500 if recommendation generation fails
    """
    try:
        recommendations = await recommendation_service.get_recommendations(request)
        return recommendations
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health Check for Recommendation Service",
    description="Check if the recommendation service is operational and can connect to Gemini API"
)
async def health_check():
    """
    Health check endpoint for the recommendation service.
    
    Returns:
        Status information about the service
    """
    return {
        "status": "healthy",
        "service": "recommendation-service",
        "model": "gemini-2.0-flash-exp",
        "grounding": "google-search",
        "features": [
            "blog recommendations",
            "youtube recommendations",
            "website recommendations",
            "course recommendations",
            "documentation recommendations"
        ]
    }


@router.post(
    "/bulk-generate",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Generate Recommendations for Multiple Topics",
    description="""
    Generate recommendations for multiple topics in a single request.
    
    This endpoint is useful when you need recommendations for several related topics
    and want to minimize API calls.
    
    Authentication: Required (JWT token)
    """,
    responses={
        200: {
            "description": "Successfully generated recommendations for all topics"
        },
        401: {
            "description": "Unauthorized - Invalid or missing authentication token"
        },
        500: {
            "description": "Internal Server Error - Failed to generate some recommendations"
        }
    }
)
async def bulk_generate_recommendations(
    topics: List[str],
    resource_types: Optional[List[Literal["blog", "youtube", "website", "course", "documentation"]]] = None,
    count: int = 5,
    current_user: CurrentUser = Depends(get_current_user)
) -> dict:
    """
    Generate recommendations for multiple topics.
    
    Args:
        topics: List of topics to generate recommendations for
        resource_types: Optional list of resource types to filter
        count: Number of recommendations per topic
        current_user: Authenticated user from JWT token
        
    Returns:
        Dictionary mapping topics to their recommendations
        
    Raises:
        HTTPException: 500 if any recommendation generation fails
    """
    results = {}
    errors = {}
    
    for topic in topics:
        try:
            request = RecommendationRequest(
                topic=topic,
                resource_types=resource_types,
                count=count
            )
            recommendations = await recommendation_service.get_recommendations(request)
            results[topic] = recommendations
        except Exception as e:
            errors[topic] = str(e)
    
    return {
        "results": results,
        "errors": errors if errors else None,
        "total_topics": len(topics),
        "successful": len(results),
        "failed": len(errors)
    }
