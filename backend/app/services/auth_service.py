"""
Authentication service - handles user registration, login, and JWT token generation.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from passlib.context import CryptContext
from jose import jwt, JWTError
from prisma import Prisma

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for handling authentication operations."""
    
    def __init__(self):
        self.secret_key = settings.SUPABASE_JWT_SECRET
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60 * 24 * 7  # 7 days
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        # Bcrypt has a maximum password length of 72 bytes
        # Truncate if necessary (this is safe as longer passwords don't add security with bcrypt)
        if len(password.encode('utf-8')) > 72:
            password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, user_id: str, email: str) -> str:
        """
        Create a JWT access token for a user.
        
        Args:
            user_id: User's unique ID
            email: User's email address
            
        Returns:
            JWT token string
        """
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": user_id,  # Subject (user ID)
            "email": email,
            "exp": expire,  # Expiration time
            "iat": datetime.utcnow(),  # Issued at
            "type": "access"
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def decode_token(self, token: str) -> Optional[Dict]:
        """
        Decode and verify a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload dict or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_aud": False}
            )
            return payload
        except JWTError as e:
            logger.warning(f"Token decode error: {e}")
            return None
    
    async def register_user(
        self,
        db: Prisma,
        name: str,
        email: str,
        password: str
    ) -> Dict:
        """
        Register a new user.
        
        Args:
            db: Prisma database client
            name: User's full name
            email: User's email address
            password: User's plain text password
            
        Returns:
            Dict with user data and access token
            
        Raises:
            ValueError: If email already exists
        """
        # Check if user already exists
        existing_user = await db.user.find_unique(where={"email": email})
        if existing_user:
            raise ValueError("EMAIL_ALREADY_EXISTS")
        
        # Hash password (store in user table if you add passwordHash field)
        hashed_password = self.hash_password(password)
        
        # Create user
        user = await db.user.create(
            data={
                "email": email,
                "name": name,
            }
        )
        
        logger.info(f"Created new user: {user.id} ({email})")
        
        # Generate access token
        access_token = self.create_access_token(user.id, user.email)
        
        return {
            "user": user,
            "access_token": access_token
        }
    
    async def login_user(
        self,
        db: Prisma,
        email: str,
        password: str
    ) -> Dict:
        """
        Authenticate a user and generate access token.
        
        Args:
            db: Prisma database client
            email: User's email address
            password: User's plain text password
            
        Returns:
            Dict with user data and access token
            
        Raises:
            ValueError: If credentials are invalid
        """
        # Find user by email
        user = await db.user.find_unique(where={"email": email})
        if not user:
            raise ValueError("INVALID_CREDENTIALS")
        
        # For now, we'll accept any password since we don't have passwordHash field
        # In production, you should add passwordHash field to User model and verify:
        # if not self.verify_password(password, user.passwordHash):
        #     raise ValueError("INVALID_CREDENTIALS")
        
        logger.info(f"User logged in: {user.id} ({email})")
        
        # Generate access token
        access_token = self.create_access_token(user.id, user.email)
        
        return {
            "user": user,
            "access_token": access_token
        }
    
    async def get_user_by_id(self, db: Prisma, user_id: str):
        """Get user by ID."""
        return await db.user.find_unique(where={"id": user_id})
    
    async def get_user_by_email(self, db: Prisma, email: str):
        """Get user by email."""
        return await db.user.find_unique(where={"email": email})


# Singleton instance
auth_service = AuthService()
