"""
Configuration settings for the MCP server
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings"""
    
    # Server settings
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    allowed_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    
    # GitHub settings
    github_token: str = Field(..., description="GitHub personal access token")
    github_api_url: str = Field(default="https://api.github.com", description="GitHub API URL")
    
    # LLM settings
    openai_api_key: str = Field(..., description="OpenAI API key")
    llm_model: str = Field(default="gpt-4", description="LLM model to use")
    
    # Conversion settings
    max_file_size: int = Field(default=10000, description="Maximum file size to process (bytes)")
    max_files_per_repo: int = Field(default=50, description="Maximum files to process per repository")
    
    # Kubernetes settings
    namespace: str = Field(default="default", description="Kubernetes namespace")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()