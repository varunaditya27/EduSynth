"""
Unsplash API client for fetching images.
"""
from typing import Optional
from app.core.config import settings


class UnsplashClient:
    """Client for searching and downloading images from Unsplash."""
    
    def __init__(self):
        """Initialize Unsplash client with API credentials."""
        self.access_key = settings.UNSPLASH_ACCESS_KEY
        self.secret_key = settings.UNSPLASH_SECRET_KEY
    
    async def search_image(self, query: str) -> Optional[dict]:
        """
        Search for an image on Unsplash.
        
        Args:
            query: Search query string
            
        Returns:
            Dictionary with keys: url, author, source
            Returns None if no suitable image found
            
        TODO: Implement actual Unsplash API search
        """
        # TODO: Implement
        # - Use httpx to call Unsplash API
        # - Search for relevant image with query
        # - Return first suitable result with attribution
        return {
            "url": f"https://placeholder.unsplash.com/{query}",
            "author": "Placeholder Author",
            "source": "unsplash",
        }