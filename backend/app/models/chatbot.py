# backend/app/models/chatbot.py

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class ChatMessage(BaseModel):
    """A single message in the conversation."""
    
    role: Literal["user", "assistant", "system"] = Field(
        ...,
        description="Role of the message sender"
    )
    
    content: str = Field(
        ...,
        description="Content of the message",
        min_length=1,
        max_length=10000
    )
    
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="When the message was created"
    )


class ChatRequest(BaseModel):
    """Request model for chatbot conversation."""
    
    message: str = Field(
        ...,
        description="User's message to the chatbot",
        min_length=1,
        max_length=5000,
        examples=["Tell me more about photosynthesis", "Can you explain this in simpler terms?"]
    )
    
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=None,
        description="Previous messages in the conversation for context",
        max_length=50
    )
    
    topic_context: Optional[str] = Field(
        default=None,
        description="The lecture topic or context for the conversation",
        max_length=500,
        examples=["Photosynthesis for 10th grade students", "Introduction to Machine Learning"]
    )
    
    lecture_id: Optional[str] = Field(
        default=None,
        description="Optional lecture ID for retrieving context"
    )


class ChatResponse(BaseModel):
    """Response model from the chatbot."""
    
    message: str = Field(
        ...,
        description="Chatbot's response message"
    )
    
    conversation_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for this conversation session"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the response was generated"
    )
    
    tokens_used: Optional[int] = Field(
        default=None,
        description="Number of tokens used for this response"
    )
    
    model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Model used for generating the response"
    )


class ConversationSession(BaseModel):
    """A complete conversation session."""
    
    session_id: str = Field(
        ...,
        description="Unique session identifier"
    )
    
    user_id: Optional[str] = Field(
        default=None,
        description="User ID if authenticated"
    )
    
    topic_context: Optional[str] = Field(
        default=None,
        description="Topic context for the conversation"
    )
    
    messages: List[ChatMessage] = Field(
        default_factory=list,
        description="All messages in the session"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Session start time"
    )
    
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last activity time"
    )


class ChatError(BaseModel):
    """Error response for chatbot failures."""
    
    error: str = Field(
        ...,
        description="Error message"
    )
    
    detail: Optional[str] = Field(
        default=None,
        description="Detailed error information"
    )
    
    retry_after: Optional[int] = Field(
        default=None,
        description="Seconds to wait before retrying (if rate limited)"
    )
