"""
MCP Server for converting shell scripts to Python code
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import structlog

from .config import settings
from .services.github_service import GitHubService
from .services.llm_service import LLMService
from .services.conversion_service import ConversionService
from .models.schemas import ConversionRequest, ConversionResponse, HealthResponse
from .utils.logging import setup_logging

# Setup structured logging
setup_logging()
logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting MCP GitHub Converter Server")
    
    # Initialize services
    github_service = GitHubService(settings.github_token)
    llm_service = LLMService(settings.openai_api_key, settings.llm_model)
    conversion_service = ConversionService(github_service, llm_service)
    
    # Store services in app state
    app.state.github_service = github_service
    app.state.llm_service = llm_service
    app.state.conversion_service = conversion_service
    
    yield
    
    logger.info("Shutting down MCP GitHub Converter Server")

app = FastAPI(
    title="MCP GitHub Shell to Python Converter",
    description="Converts shell scripts to Python code and creates pull requests",
    version="1.0.0",
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

@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "message": "MCP GitHub Shell to Python Converter",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check GitHub service
        github_healthy = await app.state.github_service.health_check()
        
        # Check LLM service
        llm_healthy = await app.state.llm_service.health_check()
        
        overall_status = "healthy" if github_healthy and llm_healthy else "unhealthy"
        
        return HealthResponse(
            status=overall_status,
            services={
                "github": "healthy" if github_healthy else "unhealthy",
                "llm": "healthy" if llm_healthy else "unhealthy"
            }
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/convert", response_model=ConversionResponse)
async def convert_repository(
    request: ConversionRequest,
    background_tasks: BackgroundTasks
):
    """Convert shell scripts in a repository to Python and create PR"""
    try:
        logger.info(
            "Starting conversion request",
            repo_owner=request.repo_owner,
            repo_name=request.repo_name
        )
        
        # Start conversion process in background
        task_id = f"{request.repo_owner}/{request.repo_name}-{asyncio.get_event_loop().time()}"
        
        background_tasks.add_task(
            app.state.conversion_service.process_repository,
            request.repo_owner,
            request.repo_name,
            request.branch or "main",
            request.target_branch,
            task_id
        )
        
        return ConversionResponse(
            task_id=task_id,
            status="started",
            message="Conversion process started. Check logs for progress."
        )
        
    except Exception as e:
        logger.error("Conversion request failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

@app.get("/status/{task_id}")
async def get_conversion_status(task_id: str):
    """Get status of a conversion task"""
    # In a production environment, you'd store task status in a database
    # For now, return a simple response
    return {"task_id": task_id, "status": "processing"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug
    )