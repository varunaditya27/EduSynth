# backend/app/models/recommendations.py

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Literal
from datetime import datetime


class RecommendationRequest(BaseModel):
    """Request model for getting learning resource recommendations."""
    
    topic: str = Field(
        ...,
        description="The topic or subject for which recommendations are needed",
        min_length=3,
        max_length=500,
        examples=["Machine Learning Basics", "Photosynthesis for 10th grade"]
    )
    
    resource_types: Optional[List[Literal["blog", "youtube", "website", "course", "documentation"]]] = Field(
        default=["blog", "youtube", "website"],
        description="Types of resources to recommend"
    )
    
    count: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of recommendations to return"
    )
    
    audience_level: Optional[Literal["beginner", "intermediate", "advanced", "all"]] = Field(
        default="all",
        description="Target audience level for the recommendations"
    )


class ResourceRecommendation(BaseModel):
    """A single recommended learning resource."""
    
    title: str = Field(
        ...,
        description="Title of the recommended resource"
    )
    
    url: str = Field(
        ...,
        description="URL to the resource (verified from Google Search)"
    )
    
    description: str = Field(
        ...,
        description="Brief description of what the resource covers"
    )
    
    resource_type: Literal["blog", "youtube", "website", "course", "documentation"] = Field(
        ...,
        description="Type of the resource"
    )
    
    relevance_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Relevance score for the recommendation (0-1)"
    )
    
    author_or_source: Optional[str] = Field(
        default=None,
        description="Author name or source organization"
    )


class RecommendationResponse(BaseModel):
    """Response model containing recommended learning resources."""
    
    topic: str = Field(
        ...,
        description="The topic for which recommendations were generated"
    )
    
    recommendations: List[ResourceRecommendation] = Field(
        ...,
        description="List of recommended resources"
    )
    
    total_count: int = Field(
        ...,
        description="Total number of recommendations returned"
    )
    
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when recommendations were generated"
    )
    
    search_query_used: Optional[str] = Field(
        default=None,
        description="The actual search query used for grounding"
    )


class RecommendationError(BaseModel):
    """Error response for recommendation failures."""
    
    error: str = Field(
        ...,
        description="Error message"
    )
    
    detail: Optional[str] = Field(
        default=None,
        description="Detailed error information"
    )
