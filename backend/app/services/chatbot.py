# backend/app/services/chatbot.py

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from groq import Groq

from app.core.config import settings
from app.models.chatbot import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    ConversationSession
)


class ChatbotService:
    """
    AI Assistant chatbot service using Groq API with Llama 3.3 70B Versatile model.
    Provides contextual conversations about lecture topics.
    """
    
    def __init__(self):
        """Initialize the Groq client with API key."""
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"
        self.max_tokens = 2048
        self.temperature = 0.7
        
        # In-memory session storage (in production, use Redis or database)
        self.sessions: Dict[str, ConversationSession] = {}
    
    async def chat(
        self,
        request: ChatRequest,
        user_id: Optional[str] = None
    ) -> ChatResponse:
        """
        Process a chat message and generate a response.
        
        Args:
            request: Chat request with message and optional context
            user_id: Optional user ID for session management
            
        Returns:
            ChatResponse with the assistant's reply
            
        Raises:
            Exception: If the API call fails
        """
        try:
            # Fetch lecture context if lecture_id is provided
            if request.lecture_id and not request.lecture_context:
                request.lecture_context = await self._fetch_lecture_context(request.lecture_id)
            
            # Build conversation messages
            messages = self._build_messages(request)
            
            # Call Groq API
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=0.9,
                stream=False
            )
            
            # Extract response
            assistant_message = completion.choices[0].message.content
            tokens_used = completion.usage.total_tokens if completion.usage else None
            
            # Create response
            response = ChatResponse(
                message=assistant_message,
                timestamp=datetime.utcnow(),
                tokens_used=tokens_used,
                model=self.model
            )
            
            return response
            
        except Exception as e:
            raise Exception(f"Chatbot error: {str(e)}")
    
    async def stream_chat(
        self,
        request: ChatRequest,
        user_id: Optional[str] = None
    ):
        """
        Stream chat responses for real-time interaction.
        
        Args:
            request: Chat request with message and optional context
            user_id: Optional user ID for session management
            
        Yields:
            Chunks of the assistant's response
        """
        try:
            # Fetch lecture context if lecture_id is provided
            if request.lecture_id and not request.lecture_context:
                request.lecture_context = await self._fetch_lecture_context(request.lecture_id)
            
            # Build conversation messages
            messages = self._build_messages(request)
            
            # Stream from Groq API
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=0.9,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            raise Exception(f"Chatbot streaming error: {str(e)}")
    
    async def _fetch_lecture_context(self, lecture_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch lecture details and slides for context.
        
        Args:
            lecture_id: ID of the lecture
            
        Returns:
            Dictionary with lecture context or None if not found
        """
        try:
            from app.db import get_client
            from pathlib import Path
            import json
            
            # Get database client
            db = await get_client()
            
            # Fetch lecture with slides
            lecture = await db.lecture.find_unique(
                where={"id": lecture_id},
                include={"slides": True}
            )
            
            if not lecture:
                return None
            
            context = {
                "topic": lecture.topic,
                "audience": lecture.targetAudience,
                "duration": lecture.desiredLength,
                "theme": lecture.visualTheme,
                "slides": []
            }
            
            # Try to load generated slides JSON for richer context
            if lecture.slides:
                for slide in lecture.slides:
                    context["slides"].append({
                        "index": slide.slideIndex,
                        "title": slide.title,
                        "points": slide.keyPoints or [],
                        "narration": slide.narration
                    })
            else:
                # Try to load from JSON file if available
                try:
                    slides_dir = Path(__file__).resolve().parents[3] / "ai_generation" / "output" / "slides"
                    # Find most recent JSON file (this is a fallback)
                    json_files = sorted(slides_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
                    if json_files:
                        with open(json_files[0], 'r', encoding='utf-8') as f:
                            slides_data = json.load(f)
                            context["slides"] = slides_data.get("slides", [])
                except Exception:
                    pass
            
            return context
            
        except Exception as e:
            print(f"Error fetching lecture context: {e}")
            return None
    
    def _build_messages(self, request: ChatRequest) -> List[Dict[str, str]]:
        """
        Build the message list for the Groq API call.
        
        Args:
            request: Chat request with context and history
            
        Returns:
            List of message dictionaries for the API
        """
        messages = []
        
        # Add system message with context
        system_message = self._create_system_message(
            request.topic_context,
            request.lecture_context
        )
        messages.append({"role": "system", "content": system_message})
        
        # Add conversation history if provided
        if request.conversation_history:
            for msg in request.conversation_history[-20:]:  # Keep last 20 messages
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": request.message
        })
        
        return messages
    
    def _create_system_message(
        self,
        topic_context: Optional[str] = None,
        lecture_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create the system message that defines the AI assistant's behavior.
        
        Args:
            topic_context: Optional topic context for the conversation
            
        Returns:
            System message string
        """
        base_prompt = """You are an intelligent AI assistant for EduSynth, an AI-powered lecture generation platform. Your role is to help users understand topics, refine their ideas, and create better educational content.

Your capabilities:
- Answer questions about any educational topic clearly and accurately
- Help users refine their lecture topics and structure
- Provide explanations at different difficulty levels (beginner, intermediate, advanced)
- Suggest related topics and learning resources
- Offer guidance on creating effective educational content
- Break down complex concepts into digestible parts

Your personality:
- Friendly, encouraging, and patient
- Clear and concise in explanations
- Adapt your language to the user's level
- Ask clarifying questions when needed
- Provide examples to illustrate concepts

Guidelines:
- Keep responses focused and relevant
- Use bullet points and structured formatting when helpful
- If you don't know something, admit it honestly
- Encourage users to explore and learn more
- Be supportive of their educational goals"""

        context_additions = []
        
        if topic_context:
            context_additions.append(f"""

Current Context:
The user is working on a lecture about: "{topic_context}"
""")
        
        if lecture_context:
            context_additions.append(f"""

Lecture Details:
- Topic: {lecture_context.get('topic', 'N/A')}
- Target Audience: {lecture_context.get('audience', 'General audience')}
- Duration: {lecture_context.get('duration', 'N/A')} minutes
- Theme: {lecture_context.get('theme', 'N/A')}
""")
            
            # Add slide content if available
            if lecture_context.get('slides'):
                slides_summary = "\n".join([
                    f"  Slide {slide.get('index', i)}: {slide.get('title', 'Untitled')}"
                    for i, slide in enumerate(lecture_context['slides'][:10], 1)  # First 10 slides
                ])
                context_additions.append(f"""

Lecture Slide Structure:
{slides_summary}
{"... (more slides)" if len(lecture_context['slides']) > 10 else ""}

You have access to the full slide content including titles, key points, and narration.
Use this to provide specific, contextual answers about the lecture content.
""")
        
        if context_additions:
            context_addition = "".join(context_additions) + """

Please provide responses that are relevant to this context while also being helpful for their broader educational goals."""
            return base_prompt + context_addition
        
        return base_prompt
    
    def create_session(
        self,
        user_id: Optional[str] = None,
        topic_context: Optional[str] = None
    ) -> ConversationSession:
        """
        Create a new conversation session.
        
        Args:
            user_id: Optional user ID
            topic_context: Optional topic context
            
        Returns:
            New ConversationSession
        """
        session = ConversationSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            topic_context=topic_context,
            messages=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        Retrieve a conversation session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            ConversationSession if found, None otherwise
        """
        return self.sessions.get(session_id)
    
    def add_message_to_session(
        self,
        session_id: str,
        message: ChatMessage
    ) -> bool:
        """
        Add a message to an existing session.
        
        Args:
            session_id: Session identifier
            message: Message to add
            
        Returns:
            True if successful, False if session not found
        """
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        session.messages.append(message)
        session.updated_at = datetime.utcnow()
        return True
    
    def clear_old_sessions(self, max_age_hours: int = 24):
        """
        Clear sessions older than specified hours.
        
        Args:
            max_age_hours: Maximum age of sessions to keep
        """
        now = datetime.utcnow()
        expired_sessions = [
            session_id
            for session_id, session in self.sessions.items()
            if (now - session.updated_at).total_seconds() > (max_age_hours * 3600)
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]


# Singleton instance
chatbot_service = ChatbotService()
