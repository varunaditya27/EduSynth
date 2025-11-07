"""
Database client singleton for Prisma.
"""
from prisma import Prisma

# Module-level singleton
prisma = Prisma()


async def get_client() -> Prisma:
    """
    Get the Prisma client, connecting if not already connected.
    Safe to call multiple times.
    """
    if not prisma.is_connected():
        await prisma.connect()
    return prisma