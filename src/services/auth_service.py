"""
Authentication and authorization service
"""
import secrets
import bcrypt
from cryptography.fernet import Fernet
from typing import Optional
import structlog
from sqlalchemy.orm import Session
from ..models.database import User, get_db
from ..config import settings
import os

logger = structlog.get_logger()

class AuthService:
    """Service for user authentication and token management"""
    
    def __init__(self):
        # Encryption key for GitHub tokens (store in environment)
        self.encryption_key = os.getenv("ENCRYPTION_KEY", Fernet.generate_key()).encode()
        self.cipher = Fernet(self.encryption_key)
    
    def generate_api_key(self) -> str:
        """Generate a secure API key for user"""
        return f"ccmcp_{secrets.token_urlsafe(32)}"
    
    def encrypt_github_token(self, token: str) -> str:
        """Encrypt GitHub PAT token"""
        return self.cipher.encrypt(token.encode()).decode()
    
    def decrypt_github_token(self, encrypted_token: str) -> str:
        """Decrypt GitHub PAT token"""
        return self.cipher.decrypt(encrypted_token.encode()).decode()
    
    async def create_user(
        self, 
        db: Session,
        email: str, 
        github_username: str,
        github_token: str
    ) -> User:
        """Create a new user with encrypted GitHub token"""
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                raise ValueError("User with this email already exists")
            
            # Encrypt GitHub token
            encrypted_token = self.encrypt_github_token(github_token)
            
            # Generate API key
            api_key = self.generate_api_key()
            
            # Create user
            user = User(
                email=email,
                github_username=github_username,
                github_token_encrypted=encrypted_token,
                api_key=api_key
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info("User created successfully", email=email, github_username=github_username)
            return user
            
        except Exception as e:
            db.rollback()
            logger.error("Failed to create user", email=email, error=str(e))
            raise
    
    async def authenticate_user(self, db: Session, api_key: str) -> Optional[User]:
        """Authenticate user by API key"""
        try:
            user = db.query(User).filter(
                User.api_key == api_key,
                User.is_active == True
            ).first()
            
            if user:
                logger.info("User authenticated", user_id=str(user.id), email=user.email)
            else:
                logger.warning("Authentication failed", api_key=api_key[:10] + "...")
            
            return user
            
        except Exception as e:
            logger.error("Authentication error", error=str(e))
            return None
    
    async def get_user_github_token(self, user: User) -> str:
        """Get decrypted GitHub token for user"""
        if not user.github_token_encrypted:
            raise ValueError("User has no GitHub token configured")
        
        return self.decrypt_github_token(user.github_token_encrypted)
    
    async def update_github_token(
        self, 
        db: Session,
        user: User, 
        new_token: str
    ) -> User:
        """Update user's GitHub token"""
        try:
            encrypted_token = self.encrypt_github_token(new_token)
            user.github_token_encrypted = encrypted_token
            
            db.commit()
            db.refresh(user)
            
            logger.info("GitHub token updated", user_id=str(user.id))
            return user
            
        except Exception as e:
            db.rollback()
            logger.error("Failed to update GitHub token", user_id=str(user.id), error=str(e))
            raise
