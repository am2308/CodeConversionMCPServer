"""
Pydantic models for request/response schemas
"""
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime

class ConversionRequest(BaseModel):
    """Request model for code conversion"""
    repo_owner: str = Field(..., description="GitHub repository owner/username")
    repo_name: str = Field(..., description="GitHub repository name")
    branch: str = Field(default="main", description="Source branch to convert from")
    target_branch: Optional[str] = Field(default=None, description="Target branch for PR (auto-generated if not provided)")
    include_patterns: Optional[List[str]] = Field(default=None, description="File patterns to include (e.g., ['*.sh', '*.ts']). If None, includes all supported file types")
    exclude_patterns: Optional[List[str]] = Field(default=None, description="File patterns to exclude (e.g., ['*.test.*', 'node_modules/**'])")
    target_language: str = Field(default="python", description="Target language for conversion")
    source_languages: Optional[List[str]] = Field(default=None, description="Source languages to convert (e.g., ['shell', 'typescript']). If None, auto-detects and converts all supported languages")
    
    class Config:
        json_schema_extra = {
            "example": {
                "repo_owner": "am2308",
                "repo_name": "my-scripts",
                "branch": "main"
            }
        }

class ConversionResponse(BaseModel):
    """Response model for conversion request"""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Task status")
    message: str = Field(..., description="Status message")

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Overall health status")
    services: Dict[str, str] = Field(..., description="Individual service health")

class FileConversion(BaseModel):
    """Model for individual file conversion"""
    original_path: str = Field(..., description="Original file path")
    converted_path: str = Field(..., description="Converted file path")
    original_content: str = Field(..., description="Original shell script content")
    converted_content: str = Field(..., description="Converted Python content")
    source_language: str = Field(..., description="Source programming language")
    target_language: str = Field(..., description="Target programming language")
    conversion_notes: Optional[str] = Field(default=None, description="Conversion notes")

# Multi-tenant schemas
class UserRegistrationRequest(BaseModel):
    """User registration request"""
    email: str
    github_username: str
    # GitHub token will be handled via OAuth/App installation
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "github_username": "john_doe"
            }
        }

class GitHubAuthRequest(BaseModel):
    """GitHub OAuth callback request"""
    code: str
    state: str

class UserRegistrationResponse(BaseModel):
    """User registration response"""
    user_id: str
    api_key: str
    github_auth_url: str  # URL to complete GitHub App installation
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "api_key": "ccmcp_xxxxxxxxxxxxx",
                "github_auth_url": "https://github.com/apps/your-app-name/installations/new",
                "message": "User registered successfully. Please complete GitHub App installation using the provided URL."
            }
        }

class JobStatusResponse(BaseModel):
    """Job status response"""
    job_id: str
    status: str  # pending, processing, completed, failed
    repo_owner: str
    repo_name: str
    source_branch: str
    target_branch: str
    files_processed: int
    files_converted: int
    pr_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "repo_owner": "john-doe",
                "repo_name": "my-project",
                "source_branch": "main",
                "target_branch": "convert-to-python",
                "files_processed": 5,
                "files_converted": 5,
                "pr_url": "https://github.com/john-doe/my-project/pull/1",
                "error_message": None,
                "created_at": "2025-01-01T10:00:00Z",
                "started_at": "2025-01-01T10:01:00Z",
                "completed_at": "2025-01-01T10:05:00Z"
            }
        }