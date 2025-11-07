# backend/app/routers/chatbot.py

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from typing import Optional

from app.models.chatbot import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    ConversationSession,
    ChatError
)
from app.services.chatbot import chatbot_service
from app.deps.auth import get_current_user, CurrentUser


router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with AI Assistant",
    description="""
    Send a message to the AI assistant and receive a contextual response.
    
    The chatbot uses Llama 3.3 70B Versatile model via Groq API to provide:
    - Contextual responses based on lecture topics
    - Educational explanations and guidance
    - Topic refinement suggestions
    - Learning resource recommendations
    - Multi-turn conversations with history
    
    Features:
    - Maintains conversation context through history
    - Adapts responses to topic context
    - Provides clear, educational explanations
    - Supports follow-up questions
    
    Authentication: Required (JWT token)
    """,
    responses={
        200: {
            "description": "Successfully generated response",
            "model": ChatResponse
        },
        401: {
            "description": "Unauthorized - Invalid or missing authentication token"
        },
        422: {
            "description": "Validation Error - Invalid request parameters"
        },
        500: {
            "description": "Internal Server Error - Failed to generate response",
            "model": ChatError
        }
    }
)
async def chat(
    request: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user)
) -> ChatResponse:
    """
    Send a message to the AI assistant and get a response.
    
    Args:
        request: Chat request with message, optional history and context
        current_user: Authenticated user from JWT token
        
    Returns:
        ChatResponse with the assistant's reply
        
    Raises:
        HTTPException: 500 if chat generation fails
    """
    try:
        response = await chatbot_service.chat(
            request=request,
            user_id=current_user.user_id
        )
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate chat response: {str(e)}"
        )


@router.post(
    "/chat/stream",
    status_code=status.HTTP_200_OK,
    summary="Stream Chat Response",
    description="""
    Stream the AI assistant's response in real-time for a more interactive experience.
    
    This endpoint returns a Server-Sent Events (SSE) stream that delivers the response
    token by token as it's generated, providing immediate feedback to users.
    
    Use this for:
    - Real-time chat interfaces
    - Progressive response display
    - Better perceived performance
    - Interactive user experience
    
    Authentication: Required (JWT token)
    """,
    responses={
        200: {
            "description": "Stream of response chunks",
            "content": {"text/event-stream": {}}
        },
        401: {
            "description": "Unauthorized - Invalid or missing authentication token"
        },
        500: {
            "description": "Internal Server Error - Failed to stream response"
        }
    }
)
async def stream_chat(
    request: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Stream chat response in real-time.
    
    Args:
        request: Chat request with message, optional history and context
        current_user: Authenticated user from JWT token
        
    Returns:
        StreamingResponse with text/event-stream content
        
    Raises:
        HTTPException: 500 if streaming fails
    """
    try:
        async def generate():
            async for chunk in chatbot_service.stream_chat(
                request=request,
                user_id=current_user.user_id
            ):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stream chat response: {str(e)}"
        )


@router.post(
    "/session/create",
    response_model=ConversationSession,
    status_code=status.HTTP_201_CREATED,
    summary="Create Conversation Session",
    description="""
    Create a new conversation session to maintain context across multiple messages.
    
    Sessions help maintain:
    - Conversation history
    - Topic context
    - User preferences
    - Multi-turn dialogue state
    
    Use this when starting a new conversation or topic discussion.
    
    Authentication: Required (JWT token)
    """,
    responses={
        201: {
            "description": "Session created successfully",
            "model": ConversationSession
        },
        401: {
            "description": "Unauthorized - Invalid or missing authentication token"
        }
    }
)
async def create_session(
    topic_context: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user)
) -> ConversationSession:
    """
    Create a new conversation session.
    
    Args:
        topic_context: Optional topic context for the conversation
        current_user: Authenticated user from JWT token
        
    Returns:
        New ConversationSession with unique session_id
    """
    session = chatbot_service.create_session(
        user_id=current_user.user_id,
        topic_context=topic_context
    )
    return session


@router.get(
    "/session/{session_id}",
    response_model=ConversationSession,
    status_code=status.HTTP_200_OK,
    summary="Get Conversation Session",
    description="""
    Retrieve an existing conversation session by ID.
    
    Returns the complete session including:
    - All message history
    - Topic context
    - Session metadata
    - Timestamps
    
    Authentication: Required (JWT token)
    """,
    responses={
        200: {
            "description": "Session retrieved successfully",
            "model": ConversationSession
        },
        404: {
            "description": "Session not found"
        },
        401: {
            "description": "Unauthorized - Invalid or missing authentication token"
        }
    }
)
async def get_session(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user)
) -> ConversationSession:
    """
    Get an existing conversation session.
    
    Args:
        session_id: Session identifier
        current_user: Authenticated user from JWT token
        
    Returns:
        ConversationSession with full history
        
    Raises:
        HTTPException: 404 if session not found
    """
    session = chatbot_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Verify session belongs to user
    if session.user_id and session.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session"
        )
    
    return session


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health Check for Chatbot Service",
    description="Check if the chatbot service is operational and can connect to Groq API"
)
async def health_check():
    """
    Health check endpoint for the chatbot service.
    
    Returns:
        Status information about the service
    """
    return {
        "status": "healthy",
        "service": "chatbot-service",
        "model": "llama-3.3-70b-versatile",
        "provider": "groq",
        "features": [
            "contextual conversations",
            "topic-aware responses",
            "streaming support",
            "session management",
            "multi-turn dialogue"
        ]
    }


@router.post(
    "/quick-ask",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Quick Question (No History)",
    description="""
    Ask a quick question without maintaining conversation history.
    
    Use this for:
    - Single, standalone questions
    - Topic clarifications
    - Quick explanations
    - One-off queries
    
    This endpoint doesn't require or maintain conversation history,
    making it faster for simple questions.
    
    Authentication: Required (JWT token)
    """,
    responses={
        200: {
            "description": "Response generated successfully",
            "model": ChatResponse
        },
        401: {
            "description": "Unauthorized - Invalid or missing authentication token"
        },
        500: {
            "description": "Internal Server Error - Failed to generate response"
        }
    }
)
async def quick_ask(
    question: str,
    topic_context: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user)
) -> ChatResponse:
    """
    Ask a quick question without conversation history.
    
    Args:
        question: The user's question
        topic_context: Optional topic context
        current_user: Authenticated user from JWT token
        
    Returns:
        ChatResponse with the answer
        
    Raises:
        HTTPException: 500 if response generation fails
    """
    try:
        request = ChatRequest(
            message=question,
            topic_context=topic_context,
            conversation_history=None
        )
        
        response = await chatbot_service.chat(
            request=request,
            user_id=current_user.user_id
        )
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(e)}"
        )
