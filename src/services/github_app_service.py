"""
GitHub App Service for secure authentication and token management
"""
import jwt
import time
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import structlog
from sqlalchemy.orm import Session

from ..config import settings
from ..models.database import User

logger = structlog.get_logger()

class GitHubAppService:
    """Service for GitHub App authentication and token management"""
    
    def __init__(self):
        self.app_id = settings.github_app_id
        self.private_key_path = settings.github_app_private_key_path
        self.client_id = settings.github_client_id
        self.client_secret = settings.github_client_secret
        self.webhook_secret = settings.github_webhook_secret
        
        # Load private key
        self.private_key = self._load_private_key()
    
    def _load_private_key(self) -> Optional[str]:
        """Load GitHub App private key from file"""
        if not self.private_key_path:
            logger.warning("No GitHub App private key path configured")
            return None
            
        try:
            with open(self.private_key_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            logger.error("GitHub App private key file not found", path=self.private_key_path)
            return None
        except Exception as e:
            logger.error("Failed to load GitHub App private key", error=str(e))
            return None
    
    def generate_jwt_token(self) -> str:
        """Generate JWT token for GitHub App authentication"""
        if not self.private_key or not self.app_id:
            raise ValueError("GitHub App credentials not configured")
        
        # Token expires in 10 minutes (GitHub's maximum)
        now = int(time.time())
        payload = {
            'iat': now - 60,  # Issued 1 minute ago (for clock skew)
            'exp': now + (10 * 60),  # Expires in 10 minutes
            'iss': self.app_id  # GitHub App ID
        }
        
        token = jwt.encode(payload, self.private_key, algorithm='RS256')
        return token
    
    async def get_app_installations(self) -> list:
        """Get all installations of the GitHub App"""
        jwt_token = self.generate_jwt_token()
        
        async with httpx.AsyncClient() as client:
            headers = {
                'Authorization': f'Bearer {jwt_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'CodeConversionMCPServer/1.0'
            }
            
            response = await client.get(
                f'{settings.github_api_url}/app/installations',
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error("Failed to get app installations", 
                           status_code=response.status_code,
                           response=response.text)
                raise Exception(f"Failed to get installations: {response.status_code}")
    
    async def get_installation_by_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get installation for a specific GitHub user"""
        installations = await self.get_app_installations()
        
        for installation in installations:
            if installation.get('account', {}).get('login') == username:
                return installation
        
        return None
    
    async def get_installation_token(self, installation_id: str) -> str:
        """Alias for generate_installation_access_token for backward compatibility"""
        return await self.generate_installation_access_token(installation_id)

    async def generate_installation_access_token(self, installation_id: str) -> str:
        """Generate installation access token for repository access"""
        jwt_token = self.generate_jwt_token()
        
        async with httpx.AsyncClient() as client:
            headers = {
                'Authorization': f'Bearer {jwt_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'CodeConversionMCPServer/1.0'
            }
            
            response = await client.post(
                f'{settings.github_api_url}/app/installations/{installation_id}/access_tokens',
                headers=headers,
                json={
                    'permissions': {
                        'contents': 'write',
                        'pull_requests': 'write',
                        'metadata': 'read'
                    }
                }
            )
            
            if response.status_code == 201:
                data = response.json()
                logger.info("Generated installation access token", 
                          installation_id=installation_id,
                          expires_at=data.get('expires_at'))
                return data['token']
            else:
                logger.error("Failed to generate installation access token",
                           installation_id=installation_id,
                           status_code=response.status_code,
                           response=response.text)
                raise Exception(f"Failed to generate access token: {response.status_code}")
    
    async def get_installation_repositories(self, installation_id: str) -> list:
        """Get repositories accessible through an installation"""
        access_token = await self.generate_installation_access_token(installation_id)
        
        async with httpx.AsyncClient() as client:
            headers = {
                'Authorization': f'token {access_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'CodeConversionMCPServer/1.0'
            }
            
            response = await client.get(
                f'{settings.github_api_url}/installation/repositories',
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json().get('repositories', [])
            else:
                logger.error("Failed to get installation repositories",
                           installation_id=installation_id,
                           status_code=response.status_code)
                raise Exception(f"Failed to get repositories: {response.status_code}")
    
    async def validate_repository_access(self, username: str, repo_owner: str, repo_name: str) -> bool:
        """Validate that user has granted access to specific repository through GitHub App"""
        try:
            installation = await self.get_installation_by_user(username)
            if not installation:
                logger.warning("No GitHub App installation found for user", username=username)
                return False
            
            repositories = await self.get_installation_repositories(installation['id'])
            
            for repo in repositories:
                if (repo['owner']['login'] == repo_owner and 
                    repo['name'] == repo_name):
                    logger.info("Repository access validated", 
                              username=username,
                              repo=f"{repo_owner}/{repo_name}")
                    return True
            
            logger.warning("Repository not accessible through GitHub App",
                         username=username,
                         repo=f"{repo_owner}/{repo_name}")
            return False
            
        except Exception as e:
            logger.error("Failed to validate repository access",
                       username=username,
                       repo=f"{repo_owner}/{repo_name}",
                       error=str(e))
            return False
    
    async def get_user_github_token(self, user: User) -> str:
        """Get GitHub access token for user (via GitHub App installation)"""
        if not user.github_username:
            raise ValueError("User has no GitHub username configured")
        
        installation = await self.get_installation_by_user(user.github_username)
        if not installation:
            raise ValueError(f"No GitHub App installation found for user {user.github_username}")
        
        access_token = await self.generate_installation_access_token(installation['id'])
        return access_token
    
    def generate_oauth_url(self, state: str) -> str:
        """Generate GitHub OAuth URL for app installation"""
        if not self.client_id:
            raise ValueError("GitHub App client ID not configured")
        
        base_url = "https://github.com/login/oauth/authorize"
        params = {
            'client_id': self.client_id,
            'redirect_uri': f"{settings.base_url}/auth/github/callback",  # We'll add this to config
            'scope': 'read:user user:email',
            'state': state,
            'allow_signup': 'true'
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange OAuth code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://github.com/login/oauth/access_token',
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'CodeConversionMCPServer/1.0'
                },
                data={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'code': code
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to exchange code: {response.status_code}")
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information using access token"""
        async with httpx.AsyncClient() as client:
            headers = {
                'Authorization': f'token {access_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'CodeConversionMCPServer/1.0'
            }
            
            response = await client.get(
                f'{settings.github_api_url}/user',
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to get user info: {response.status_code}")
