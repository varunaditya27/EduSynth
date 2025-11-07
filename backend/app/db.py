# backend/app/db.py

from prisma import Prisma

# Global Prisma client instance
_client: Prisma | None = None


async def get_client() -> Prisma:
    """
    Get or create the Prisma client instance.
    
    Returns:
        Prisma: Connected Prisma client
    """
    global _client
    
    if _client is None:
        _client = Prisma()
        await _client.connect()
    
    return _client


async def disconnect_client() -> None:
    """
    Disconnect the Prisma client if connected.
    Should be called on application shutdown.
    """
    global _client
    
    if _client is not None:
        await _client.disconnect()
        _client = None