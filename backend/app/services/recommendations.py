# backend/app/services/recommendations.py

import json
from typing import List, Dict, Any
from datetime import datetime
import google.generativeai as genai

from app.core.config import settings
from app.models.recommendations import (
    RecommendationRequest,
    RecommendationResponse,
    ResourceRecommendation
)


class RecommendationService:
    """Service for generating learning resource recommendations using Gemini 2.5 Pro with Google Search grounding."""
    
    def __init__(self):
        """Initialize the Gemini client with API key."""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    async def get_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """
        Generate learning resource recommendations using Gemini with Google Search grounding.
        
        Args:
            request: The recommendation request parameters
            
        Returns:
            RecommendationResponse with verified, grounded recommendations
            
        Raises:
            Exception: If the API call fails or returns invalid data
        """
        try:
            # Construct the prompt with explicit anti-hallucination instructions
            prompt = self._build_prompt(request)
            
            # Configure generation with Google Search grounding to prevent hallucination
            generation_config = genai.GenerationConfig(
                temperature=0.3,  # Lower temperature for more factual responses
                top_p=0.8,
                top_k=40,
                max_output_tokens=4096,
                response_mime_type="application/json"
            )
            
            # Use Google Search grounding tool to ensure all URLs are real
            tools = [genai.protos.Tool(
                google_search_retrieval=genai.protos.GoogleSearchRetrieval()
            )]
            
            # Generate recommendations with grounding
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                tools=tools,
                safety_settings={
                    'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
                    'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
                    'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
                    'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
                }
            )
            
            # Parse the JSON response
            recommendations_data = json.loads(response.text)
            
            # Convert to ResourceRecommendation objects
            recommendations = [
                ResourceRecommendation(**rec)
                for rec in recommendations_data.get("recommendations", [])
            ]
            
            # Create and return the response
            return RecommendationResponse(
                topic=request.topic,
                recommendations=recommendations[:request.count],
                total_count=len(recommendations[:request.count]),
                generated_at=datetime.utcnow(),
                search_query_used=recommendations_data.get("search_query_used")
            )
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse Gemini response as JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to generate recommendations: {str(e)}")
    
    def _build_prompt(self, request: RecommendationRequest) -> str:
        """
        Build a detailed prompt for Gemini with strict anti-hallucination instructions.
        
        Args:
            request: The recommendation request
            
        Returns:
            Formatted prompt string
        """
        resource_types_str = ", ".join(request.resource_types or ["blog", "youtube", "website"])
        
        prompt = f"""You are a learning resource recommendation expert. Your task is to find REAL, VERIFIED learning resources for the topic: "{request.topic}"

CRITICAL INSTRUCTIONS - READ CAREFULLY:
1. You MUST use Google Search to find REAL, EXISTING resources
2. Every URL you provide MUST be a real, accessible link that exists on the internet
3. DO NOT create, invent, or hallucinate ANY URLs
4. DO NOT guess or make up URLs based on patterns
5. Every recommendation MUST be grounded in actual search results
6. If you cannot find enough real resources, return fewer recommendations rather than inventing fake ones
7. Verify each URL exists before including it in your response

TASK REQUIREMENTS:
- Topic: {request.topic}
- Resource Types: {resource_types_str}
- Number of recommendations: {request.count}
- Audience Level: {request.audience_level}

For each resource you find, provide:
1. title: The exact title of the resource
2. url: The REAL, VERIFIED URL (must be from Google Search results)
3. description: A brief, accurate description (2-3 sentences)
4. resource_type: One of [{resource_types_str}]
5. relevance_score: How relevant it is to the topic (0.0 to 1.0)
6. author_or_source: The author name or organization (if available)

SEARCH STRATEGY:
- For blogs: Search for "{request.topic} blog tutorial guide"
- For YouTube: Search for "{request.topic} youtube video tutorial"
- For websites: Search for "{request.topic} official documentation website"
- For courses: Search for "{request.topic} online course"

OUTPUT FORMAT (JSON):
{{
    "search_query_used": "the actual search query you used",
    "recommendations": [
        {{
            "title": "Exact resource title",
            "url": "Real, verified URL from search results",
            "description": "Accurate description of the resource",
            "resource_type": "blog|youtube|website|course|documentation",
            "relevance_score": 0.95,
            "author_or_source": "Author or organization name"
        }}
    ]
}}

REMEMBER: Only include resources that you have verified exist through Google Search. Quality over quantity!"""
        
        return prompt


# Singleton instance
recommendation_service = RecommendationService()
