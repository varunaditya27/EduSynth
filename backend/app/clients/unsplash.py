# backend/app/clients/unsplash.py

from typing import Optional, Dict
import httpx

from app.core.config import settings


class UnsplashClient:
    """
    Client for interacting with the Unsplash API to search and retrieve images.
    """
    
    def __init__(self):
        """Initialize Unsplash client with API credentials from settings."""
        self.access_key = settings.UNSPLASH_ACCESS_KEY
        self.secret_key = settings.UNSPLASH_SECRET_KEY
        self.base_url = "https://api.unsplash.com"
    
    async def search_image(self, query: str) -> Optional[Dict[str, str]]:
        """
        Search for an image on Unsplash based on a query.
        
        Args:
            query: Search query string
            
        Returns:
            Dictionary with image metadata:
            {
                "url": str,        # Direct URL to the image
                "author": str,     # Photographer name
                "source": "unsplash"
            }
            Returns None if no suitable image found or request fails.
        """
        # TODO: Implement actual Unsplash API search
        # async with httpx.AsyncClient() as client:
        #     response = await client.get(
        #         f"{self.base_url}/search/photos",
        #         params={"query": query, "per_page": 1},
        #         headers={"Authorization": f"Client-ID {self.access_key}"}
        #     )
        #     if response.status_code == 200:
        #         data = response.json()
        #         if data["results"]:
        #             photo = data["results"][0]
        #             return {
        #                 "url": photo["urls"]["regular"],
        #                 "author": photo["user"]["name"],
        #                 "source": "unsplash"
        #             }
        # return None
        
        # Placeholder return
        return {
            "url": f"https://source.unsplash.com/800x600/?{query}",
            "author": "Placeholder Author",
            "source": "unsplash"
        }