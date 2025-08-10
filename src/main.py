"""
Multi-tenant Code Conversion MCP Server
"""
import asyncio
from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
import json
import uuid
from datetime import datetime

from .config import settings
from .models.database import create_tables, get_db, SessionLocal, User, ConversionJob
from .models.schemas import (
    HealthResponse, 
    ConversionRequest, 
    ConversionResponse,
    UserRegistrationRequest,
    UserRegistrationResponse,
    GitHubAuthRequest,
    JobStatusResponse
)
from .services.auth_service import AuthService
from .services.conversion_service import ConversionService
from .services.github_service import GitHubService
from .services.github_app_service import GitHubAppService
from .services.llm_service import LLMService
from .utils.logging import setup_logging

# Setup structured logging
setup_logging()
logger = structlog.get_logger()

# Initialize services
auth_service = AuthService()
github_app_service = GitHubAppService()

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
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "authentication",
            "description": "User registration and authentication operations",
        },
        {
            "name": "conversion",
            "description": "Code conversion operations",
        },
        {
            "name": "jobs",
            "description": "Job management and status tracking",
        },
        {
            "name": "health",
            "description": "System health and status",
        },
    ],
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

@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db_healthy = True
        try:
            with SessionLocal() as db:
                db.execute(text("SELECT 1"))
        except Exception:
            db_healthy = False
        
        # Test LLM service
        llm_service = LLMService(settings.openai_api_key, settings.llm_model)
        llm_healthy = await llm_service.health_check()
        
        overall_healthy = db_healthy and llm_healthy
        
        return HealthResponse(
            status="healthy" if overall_healthy else "degraded",
            services={
                "llm": "healthy" if llm_healthy else "unhealthy",
                "database": "healthy" if db_healthy else "unhealthy"
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

@app.post("/auth/register", response_model=UserRegistrationResponse, tags=["authentication"])
async def register_user(
    request: UserRegistrationRequest,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    try:
        user = await auth_service.create_user(
            db=db,
            email=request.email,
            github_username=request.github_username
        )
        
        # Generate GitHub App installation URL
        # Use app slug (name) instead of numeric ID for the installation URL
        app_slug = settings.github_app_slug or "codeconversion"  # fallback to your app name
        github_auth_url = f"https://github.com/apps/{app_slug}/installations/new"
        
        return UserRegistrationResponse(
            user_id=str(user.id),
            api_key=user.api_key,
            github_auth_url=github_auth_url,
            message="User registered successfully. Please install the GitHub App using the provided URL to enable repository access."
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("User registration failed", error=str(e))
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/convert", response_model=ConversionResponse, tags=["conversion"])
async def convert_repository(
    request: ConversionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start code conversion job"""
    try:
        # Generate unique target branch name if not provided
        target_branch = request.target_branch
        if not target_branch:
            timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            target_branch = f"convert-to-{request.target_language}-{timestamp}"
        
        # Create job record
        job = ConversionJob(
            user_id=current_user.id,
            repo_owner=request.repo_owner,
            repo_name=request.repo_name,
            source_branch=request.branch,
            target_branch=target_branch,
            source_languages=json.dumps(request.source_languages) if request.source_languages else None,
            target_language=request.target_language,
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

@app.get("/jobs/{job_id}", response_model=JobStatusResponse, tags=["jobs"])
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

@app.get("/jobs", response_model=List[JobStatusResponse], tags=["jobs"])
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

@app.post("/auth/github/callback", tags=["authentication"])
async def github_oauth_callback(
    request: GitHubAuthRequest,
    db: Session = Depends(get_db)
):
    """Handle GitHub OAuth callback and link installation"""
    try:
        # Exchange code for access token
        token_data = await github_app_service.exchange_code_for_token(request.code)
        access_token = token_data.get('access_token')
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        # Get user info
        user_info = await github_app_service.get_user_info(access_token)
        github_username = user_info.get('login')
        
        # Find user by GitHub username
        user = db.query(User).filter(User.github_username == github_username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found. Please register first.")
        
        # Link OAuth token to user (installation will be linked via webhook)
        await auth_service.link_github_installation(
            db=db,
            user=user,
            installation_id="",  # Will be updated via webhook
            oauth_token=access_token
        )
        
        return {
            "message": "GitHub authentication successful",
            "username": github_username,
            "next_step": "Install the GitHub App on your repositories to enable code conversion"
        }
        
    except Exception as e:
        logger.error("GitHub OAuth callback failed", error=str(e))
        raise HTTPException(status_code=500, detail="Authentication failed")

@app.post("/webhooks/github", tags=["webhooks"])
async def github_webhook(
    request: dict,
    db: Session = Depends(get_db)
):
    """Handle GitHub App webhook events"""
    try:
        event_type = request.get('action')
        installation = request.get('installation', {})
        installation_id = installation.get('id')
        
        if event_type == 'created' and installation_id:
            # App was installed
            account = installation.get('account', {})
            username = account.get('login')
            
            # Find user and link installation
            user = db.query(User).filter(User.github_username == username).first()
            if user:
                await auth_service.link_github_installation(
                    db=db,
                    user=user,
                    installation_id=str(installation_id)
                )
                
                logger.info("GitHub App installation linked",
                           username=username,
                           installation_id=installation_id)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error("GitHub webhook failed", error=str(e))
        return {"status": "error"}

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
        
        # Get user's GitHub installation token
        if user.github_installation_id:
            try:
                github_token = await github_app_service.get_installation_token(user.github_installation_id)
            except Exception as e:
                logger.error("Failed to get installation token", installation_id=user.github_installation_id, error=str(e))
                # Fallback to stored token if available
                github_token = await auth_service.get_user_github_token(user)
        else:
            # Use stored token if no installation linked
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

# Configure OpenAPI security scheme
app.openapi_schema = None  # Reset to regenerate

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "API Key",
            "description": "Enter your API key obtained from user registration"
        }
    }
    
    # Add security to protected endpoints
    for path, path_item in openapi_schema["paths"].items():
        if path in ["/convert", "/jobs", "/jobs/{job_id}"]:
            for method in path_item:
                if method in ["get", "post", "put", "delete"]:
                    path_item[method]["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug
    )