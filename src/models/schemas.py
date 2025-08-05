"""
Pydantic models for request/response schemas
"""
from typing import Optional, Dict, List
from pydantic import BaseModel, Field

class ConversionRequest(BaseModel):
    """Request model for code conversion"""
    repo_owner: str = Field(..., description="GitHub repository owner")
    repo_name: str = Field(..., description="GitHub repository name")
    branch: Optional[str] = Field(default="main", description="Source branch")
    target_branch: Optional[str] = Field(default=None, description="Target branch for PR")
    include_patterns: Optional[List[str]] = Field(default=None, description="File patterns to include (if None, uses all supported extensions)")
    exclude_patterns: Optional[List[str]] = Field(default=[], description="File patterns to exclude")
    target_language: Optional[str] = Field(default="python", description="Target language for conversion")
    source_languages: Optional[List[str]] = Field(default=None, description="Source languages to convert (if None, converts all supported)")

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