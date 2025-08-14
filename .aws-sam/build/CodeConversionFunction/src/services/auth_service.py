"""
Authentication and authorization service
"""
import secrets
import bcrypt
from cryptography.fernet import Fernet
from typing import Optional
import structlog
from sqlalchemy.orm import Session
from datetime import datetime
from ..models.database import User, get_db
from ..config import settings
import os
from datetime import datetime

logger = structlog.get_logger()

class AuthService:
    """Service for user authentication and token management"""
    
    def __init__(self):
        # Encryption key for GitHub tokens (store in environment)
        encryption_key_env = os.getenv("ENCRYPTION_KEY")
        if encryption_key_env:
            # If key is provided as string, encode it to bytes
            self.encryption_key = encryption_key_env.encode()
        else:
            # Generate new key (already returns bytes)
            self.encryption_key = Fernet.generate_key()
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
        github_username: str
    ) -> User:
        """Create a new user (GitHub authentication handled separately via OAuth)"""
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                raise ValueError("User with this email already exists")
            
            # Generate API key
            api_key = self.generate_api_key()
            
            # Create user (GitHub installation will be linked later)
            user = User(
                email=email,
                github_username=github_username,
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

    async def link_github_installation(
        self, 
        db: Session, 
        user: User, 
        installation_id: str, 
        oauth_token: str = None
    ) -> User:
        """Link GitHub App installation to user"""
        try:
            if installation_id:
                user.github_installation_id = installation_id
            if oauth_token:
                encrypted_token = self.encrypt_github_token(oauth_token)
                user.github_token_encrypted = encrypted_token
            
            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            
            logger.info("GitHub installation linked", user_id=str(user.id), installation_id=installation_id)
            return user
            
        except Exception as e:
            db.rollback()
            logger.error("Failed to link GitHub installation", user_id=str(user.id), error=str(e))
            raise
        
    async def link_github_installation(
        self, 
        db: Session, 
        user: User, 
        installation_id: str, 
        oauth_token: str = None
    ) -> User:
        """Link GitHub App installation to user"""
        try:
            user.github_installation_id = installation_id
            if oauth_token:
                # Encrypt and store OAuth token if provided
                encrypted_token = self.encrypt_github_token(oauth_token)
                user.github_token_encrypted = encrypted_token
            
            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            
            logger.info("GitHub installation linked", 
                       user_id=str(user.id), 
                       installation_id=installation_id)
            return user
            
        except Exception as e:
            db.rollback()
            logger.error("Failed to link GitHub installation", 
                        user_id=str(user.id), 
                        error=str(e))
            raise
