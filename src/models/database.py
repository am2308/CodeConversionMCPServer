"""
Database models for multi-tenant code conversion service
"""
from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from typing import Optional
import os

Base = declarative_base()

class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    github_username = Column(String(255), nullable=True)
    github_token_encrypted = Column(Text, nullable=True)  # Encrypted PAT token
    api_key = Column(String(255), unique=True, nullable=False, index=True)  # User's API key
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    conversion_jobs = relationship("ConversionJob", back_populates="user")
    
class ConversionJob(Base):
    """Job tracking for code conversions"""
    __tablename__ = "conversion_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Repository details
    repo_owner = Column(String(255), nullable=False)
    repo_name = Column(String(255), nullable=False)
    source_branch = Column(String(255), default="main")
    target_branch = Column(String(255), nullable=False)
    
    # Conversion details
    source_languages = Column(Text, nullable=True)  # JSON array
    target_language = Column(String(50), default="python")
    
    # Job status
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    pr_url = Column(String(500), nullable=True)
    
    # Metrics
    files_processed = Column(Integer, default=0)
    files_converted = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="conversion_jobs")

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/codeconv")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
