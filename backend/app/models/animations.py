# backend/app/models/animations.py
"""
Models for interactive animation metadata.
Defines the structure for step-by-step animated learning experiences.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum


class AnimationType(str, Enum):
    """Types of animations that can be applied."""
    FADE_IN = "fade_in"
    SLIDE_IN = "slide_in"
    SCALE_UP = "scale_up"
    DRAW = "draw"  # For lines, arrows, diagrams
    TYPEWRITER = "typewriter"  # For text
    BOUNCE = "bounce"
    ROTATE = "rotate"
    MORPH = "morph"  # Shape transformation
    PARTICLE = "particle"  # Particle effects
    HIGHLIGHT = "highlight"


class InteractionType(str, Enum):
    """Types of user interactions."""
    CLICK_TO_REVEAL = "click_to_reveal"
    DRAG_AND_DROP = "drag_and_drop"
    HOVER_INFO = "hover_info"
    INPUT_ANSWER = "input_answer"
    MULTIPLE_CHOICE = "multiple_choice"
    SLIDER_ADJUST = "slider_adjust"
    SIMULATION = "simulation"
    AUTO_ADVANCE = "auto_advance"  # No interaction, auto-progresses


class AnimationElement(BaseModel):
    """An element that can be animated (shape, text, image, etc.)"""
    id: str = Field(..., description="Unique identifier for the element")
    type: Literal["text", "shape", "image", "diagram", "arrow", "icon", "equation"] = Field(
        ..., description="Type of visual element"
    )
    content: str = Field(..., description="Content/description of the element")
    position: dict = Field(
        default={"x": 50, "y": 50}, 
        description="Position as percentage of canvas (x: 0-100, y: 0-100)"
    )
    style: Optional[dict] = Field(
        default=None,
        description="Visual styling (color, size, font, etc.)"
    )


class AnimationStep(BaseModel):
    """A single step in an animation sequence."""
    step_number: int = Field(..., ge=1, description="Order in the sequence")
    description: str = Field(..., description="What happens in this step")
    
    elements: List[AnimationElement] = Field(
        default_factory=list,
        description="Elements that appear/animate in this step"
    )
    
    animation_type: AnimationType = Field(
        default=AnimationType.FADE_IN,
        description="How elements appear/move"
    )
    
    duration_ms: int = Field(
        default=1000, ge=100, le=5000,
        description="Duration of animation in milliseconds"
    )
    
    delay_ms: int = Field(
        default=0, ge=0,
        description="Delay before animation starts"
    )
    
    audio_segment_start: Optional[float] = Field(
        default=None,
        description="Start time in audio file for this step (seconds)"
    )
    
    audio_segment_end: Optional[float] = Field(
        default=None,
        description="End time in audio file for this step (seconds)"
    )
    
    narration_text: Optional[str] = Field(
        default=None,
        description="Text to highlight during this step"
    )


class InteractionPoint(BaseModel):
    """An interactive element that requires user action."""
    id: str = Field(..., description="Unique identifier")
    type: InteractionType = Field(..., description="Type of interaction")
    
    prompt: str = Field(..., description="Instruction shown to the user")
    
    target_element_id: Optional[str] = Field(
        default=None,
        description="ID of element this interaction affects"
    )
    
    position: dict = Field(
        default={"x": 50, "y": 50},
        description="Position of interaction trigger"
    )
    
    # For quiz/input interactions
    correct_answer: Optional[str] = Field(default=None)
    options: Optional[List[str]] = Field(default=None)
    
    # Feedback
    success_message: Optional[str] = Field(default=None)
    hint: Optional[str] = Field(default=None)
    
    # Next step control
    unlocks_step: Optional[int] = Field(
        default=None,
        description="Which animation step this interaction unlocks"
    )


class SlideAnimation(BaseModel):
    """Complete animation sequence for a single slide."""
    slide_index: int = Field(..., ge=0)
    title: str
    
    # Animation sequence
    steps: List[AnimationStep] = Field(
        default_factory=list,
        description="Ordered list of animation steps"
    )
    
    # Interactivity
    interactions: List[InteractionPoint] = Field(
        default_factory=list,
        description="Interactive elements on this slide"
    )
    
    # Metadata
    concept: str = Field(..., description="Main concept being taught")
    difficulty: Literal["easy", "medium", "hard"] = Field(default="medium")
    estimated_time_seconds: int = Field(
        default=30,
        description="Estimated time for user to complete this slide"
    )
    
    # Visual theme effects
    theme_effects: Optional[dict] = Field(
        default=None,
        description="Theme-specific animation adjustments"
    )


class LectureAnimations(BaseModel):
    """Complete animation data for entire lecture."""
    lecture_id: str
    topic: str
    audience: str
    theme: str
    
    slides: List[SlideAnimation] = Field(
        default_factory=list,
        description="Animation data for each slide"
    )
    
    # Overall metadata
    total_estimated_time_seconds: int = Field(
        default=0,
        description="Total estimated completion time"
    )
    
    interaction_count: int = Field(
        default=0,
        description="Total number of interactive elements"
    )
    
    gamification: Optional[dict] = Field(
        default=None,
        description="Gamification settings (points, badges, etc.)"
    )


class AnimationGenerationRequest(BaseModel):
    """Request to generate animations for a lecture."""
    topic: str
    audience: str
    length: str  # "5 min", "10 min", etc.
    theme: str = "Minimalist"
    
    # Animation preferences
    interaction_level: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="How many interactive elements to include"
    )
    
    animation_style: Literal["gentle", "dynamic", "professional"] = Field(
        default="dynamic",
        description="Pacing and energy of animations"
    )
    
    include_simulations: bool = Field(
        default=False,
        description="Whether to include interactive simulations"
    )
    
    include_quizzes: bool = Field(
        default=True,
        description="Whether to include quiz interactions"
    )
