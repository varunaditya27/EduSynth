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
        system_message = self._create_system_message(request.topic_context)
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
    
    def _create_system_message(self, topic_context: Optional[str] = None) -> str:
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

        if topic_context:
            context_addition = f"""

Current Context:
The user is working on a lecture about: "{topic_context}"

Please provide responses that are relevant to this topic while also being helpful for their broader educational goals."""
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
