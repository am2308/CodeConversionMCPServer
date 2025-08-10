"""
Configuration settings for the MCP server
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings"""
    
    # Server settings
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    allowed_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Database settings
    database_url: str = Field(..., description="Database connection URL")
    postgres_password: str = Field(..., description="PostgreSQL password")
    
    # Security settings
    encryption_key: str = Field(..., description="Fernet encryption key for storing sensitive data")
    
    # GitHub App settings (Secure)
    github_app_id: Optional[str] = Field(default=None, description="GitHub App ID")
    github_app_slug: Optional[str] = Field(default=None, description="GitHub App slug/name (for installation URLs)")
    github_app_private_key_path: Optional[str] = Field(default=None, description="Path to GitHub App private key")
    github_webhook_secret: Optional[str] = Field(default=None, description="GitHub App webhook secret")
    github_client_id: Optional[str] = Field(default=None, description="GitHub App client ID")
    github_client_secret: Optional[str] = Field(default=None, description="GitHub App client secret")
    
    # Legacy GitHub settings (fallback)
    github_token: Optional[str] = Field(default=None, description="GitHub personal access token (fallback only)")
    github_api_url: str = Field(default="https://api.github.com", description="GitHub API URL")
    
    # LLM settings
    openai_api_key: str = Field(..., description="OpenAI API key")
    llm_model: str = Field(default="gpt-4", description="LLM model to use")
    
    # Conversion settings
    max_file_size: int = Field(default=10000, description="Maximum file size to process (bytes)")
    max_files_per_repo: int = Field(default=50, description="Maximum files to process per repository")
    
    # Supported file extensions and their language mappings
    supported_extensions: dict = Field(
        default={
            ".sh": "shell",
            ".bash": "shell", 
            ".zsh": "shell",
            ".fish": "shell",
            ".ps1": "powershell",
            ".psm1": "powershell",
            ".psd1": "powershell",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".java": "java",
            ".scala": "scala",
            ".kt": "kotlin",
            ".swift": "swift",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".c": "c",
            ".pl": "perl",
            ".r": "r",
            ".R": "r",
            ".lua": "lua",
            ".dart": "dart",
            ".groovy": "groovy",
            ".gradle": "groovy"
        },
        description="Supported file extensions and their language mappings"
    )
    
    # Kubernetes settings
    namespace: str = Field(default="default", description="Kubernetes namespace")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()