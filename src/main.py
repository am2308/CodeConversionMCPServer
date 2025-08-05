"""
Multi-tenant Code Conversion MCP Server
"""
import asyncio
from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List
import json
import uuid
from datetime import datetime

from .config import settings
from .models.database import create_tables, get_db, User, ConversionJob
from .models.schemas import (
    HealthResponse, 
    ConversionRequest, 
    ConversionResponse,
    UserRegistrationRequest,
    UserRegistrationResponse,
    JobStatusResponse
)
from .services.auth_service import AuthService
from .services.conversion_service import ConversionService
from .services.github_service import GitHubService
from .services.llm_service import LLMService
from .utils.logging import setup_logging

# Setup structured logging
setup_logging()
logger = structlog.get_logger()

# Initialize services
auth_service = AuthService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Multi-tenant Code Conversion MCP Server")
    create_tables()
    yield
    # Shutdown
    logger.info("Shutting down Multi-tenant Code Conversion MCP Server")

# Create FastAPI app
app = FastAPI(
    title="Code Conversion MCP Server",
    description="Multi-tenant service for converting code between programming languages",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    api_key = credentials.credentials
    user = await auth_service.authenticate_user(db, api_key)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return user

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Multi-tenant Code Conversion MCP Server",
        "version": "2.0.0",
        "docs": "/docs",
        "supported_languages": list(set(settings.supported_extensions.values())),
        "endpoints": {
            "register": "/auth/register",
            "convert": "/convert",
            "jobs": "/jobs",
            "health": "/health"
        }
    }

@app.get("/supported-languages")
async def get_supported_languages():
    """Get list of supported programming languages"""
    languages = {}
    for ext, lang in settings.supported_extensions.items():
        if lang not in languages:
            languages[lang] = []
        languages[lang].append(ext)
    
    return {
        "supported_languages": languages,
        "total_languages": len(languages),
        "total_extensions": len(settings.supported_extensions)
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Test LLM service
        llm_service = LLMService(settings.openai_api_key, settings.llm_model)
        llm_healthy = await llm_service.health_check()
        
        return HealthResponse(
            status="healthy" if llm_healthy else "degraded",
            services={
                "llm": "healthy" if llm_healthy else "unhealthy",
                "database": "healthy"
            }
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthResponse(
            status="unhealthy",
            services={
                "llm": "unknown",
                "database": "unknown"
            }
        )

@app.post("/auth/register", response_model=UserRegistrationResponse)
async def register_user(
    request: UserRegistrationRequest,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    try:
        user = await auth_service.create_user(
            db=db,
            email=request.email,
            github_username=request.github_username,
            github_token=request.github_token
        )
        
        return UserRegistrationResponse(
            user_id=str(user.id),
            api_key=user.api_key,
            message="User registered successfully"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("User registration failed", error=str(e))
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/convert", response_model=ConversionResponse)
async def convert_repository(
    request: ConversionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start code conversion job"""
    try:
        # Create job record
        job = ConversionJob(
            user_id=current_user.id,
            repo_owner=request.repo_owner,
            repo_name=request.repo_name,
            source_branch=request.branch or "main",
            target_branch=request.target_branch or f"convert-to-{request.target_language or 'python'}",
            source_languages=json.dumps(request.source_languages) if request.source_languages else None,
            target_language=request.target_language or "python",
            status="pending"
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Start background conversion task
        background_tasks.add_task(
            process_conversion_job,
            job_id=str(job.id),
            user_id=str(current_user.id)
        )
        
        logger.info("Conversion job created", 
                   job_id=str(job.id), 
                   user_id=str(current_user.id),
                   repo=f"{request.repo_owner}/{request.repo_name}")
        
        return ConversionResponse(
            task_id=str(job.id),
            status="pending",
            message="Conversion job started. Use /jobs/{job_id} to check status."
        )
        
    except Exception as e:
        logger.error("Failed to start conversion", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to start conversion")

@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversion job status"""
    try:
        job = db.query(ConversionJob).filter(
            ConversionJob.id == job_id,
            ConversionJob.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobStatusResponse(
            job_id=str(job.id),
            status=job.status,
            repo_owner=job.repo_owner,
            repo_name=job.repo_name,
            source_branch=job.source_branch,
            target_branch=job.target_branch,
            files_processed=job.files_processed,
            files_converted=job.files_converted,
            pr_url=job.pr_url,
            error_message=job.error_message,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get job status", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get job status")

@app.get("/jobs", response_model=List[JobStatusResponse])
async def list_user_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10,
    offset: int = 0
):
    """List user's conversion jobs"""
    try:
        jobs = db.query(ConversionJob).filter(
            ConversionJob.user_id == current_user.id
        ).order_by(ConversionJob.created_at.desc()).offset(offset).limit(limit).all()
        
        return [
            JobStatusResponse(
                job_id=str(job.id),
                status=job.status,
                repo_owner=job.repo_owner,
                repo_name=job.repo_name,
                source_branch=job.source_branch,
                target_branch=job.target_branch,
                files_processed=job.files_processed,
                files_converted=job.files_converted,
                pr_url=job.pr_url,
                error_message=job.error_message,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at
            )
            for job in jobs
        ]
        
    except Exception as e:
        logger.error("Failed to list jobs", user_id=str(current_user.id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list jobs")

async def process_conversion_job(job_id: str, user_id: str):
    """Background task to process conversion job"""
    db = next(get_db())
    
    try:
        # Get job and user
        job = db.query(ConversionJob).filter(ConversionJob.id == job_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        
        if not job or not user:
            logger.error("Job or user not found", job_id=job_id, user_id=user_id)
            return
        
        # Update job status
        job.status = "processing"
        job.started_at = datetime.utcnow()
        db.commit()
        
        # Get user's GitHub token
        github_token = await auth_service.get_user_github_token(user)
        
        # Initialize services
        github_service = GitHubService(github_token)
        llm_service = LLMService(settings.openai_api_key, settings.llm_model)
        conversion_service = ConversionService(github_service, llm_service)
        
        # Parse source languages
        source_languages = None
        if job.source_languages:
            source_languages = json.loads(job.source_languages)
        
        # Process repository
        await conversion_service.process_repository(
            repo_owner=job.repo_owner,
            repo_name=job.repo_name,
            source_branch=job.source_branch,
            target_branch=job.target_branch,
            source_languages=source_languages,
            target_language=job.target_language,
            task_id=job_id
        )
        
        # Update job as completed
        job = db.query(ConversionJob).filter(ConversionJob.id == job_id).first()
        if job and job.status == "processing":
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            db.commit()
        
    except Exception as e:
        logger.error("Conversion job failed", job_id=job_id, error=str(e))
        
        # Update job as failed
        job = db.query(ConversionJob).filter(ConversionJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
    
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug
    )