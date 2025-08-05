"""
GitHub service for repository operations
"""
import asyncio
from typing import List, Tuple, Optional
import structlog
from github import Github, GithubException
from github.Repository import Repository
from github.ContentFile import ContentFile
from ..config import settings

logger = structlog.get_logger()

class GitHubService:
    """Service for GitHub operations"""
    
    def __init__(self, token: str):
        self.github = Github(token)
        self.token = token
    
    async def health_check(self) -> bool:
        """Check GitHub service health"""
        try:
            # Test API access
            user = self.github.get_user()
            user.login  # This will trigger an API call
            return True
        except Exception as e:
            logger.error("GitHub health check failed", error=str(e))
            return False
    
    async def get_repository(self, owner: str, name: str) -> Repository:
        """Get repository object"""
        try:
            repo = self.github.get_repo(f"{owner}/{name}")
            return repo
        except GithubException as e:
            logger.error("Failed to get repository", owner=owner, name=name, error=str(e))
            raise
    
    async def find_convertible_files(
        self, 
        repo: Repository, 
        branch: str = "main",
        source_languages: Optional[List[str]] = None
    ) -> List[Tuple[ContentFile, str]]:
        """Find all convertible files in repository"""
        convertible_files = []
        
        # Determine which extensions to look for
        target_extensions = []
        if source_languages:
            # Filter extensions based on requested source languages
            for ext, lang in settings.supported_extensions.items():
                if lang in source_languages:
                    target_extensions.append(ext)
        else:
            # Use all supported extensions
            target_extensions = list(settings.supported_extensions.keys())
        
        try:
            # Get repository contents recursively
            contents = repo.get_contents("", ref=branch)
            
            while contents:
                file_content = contents.pop(0)
                
                if file_content.type == "dir":
                    # Add directory contents to process
                    contents.extend(repo.get_contents(file_content.path, ref=branch))
                else:
                    # Check if file has a supported extension
                    for ext in target_extensions:
                        if file_content.name.endswith(ext):
                            language = settings.supported_extensions[ext]
                            convertible_files.append((file_content, language))
                            logger.info("Found convertible file", 
                                      path=file_content.path, 
                                      language=language)
                            break
            
            logger.info("File discovery complete", count=len(convertible_files))
            return convertible_files
            
        except GithubException as e:
            logger.error("Failed to find convertible files", error=str(e))
            raise
    
    async def get_file_content(self, file: ContentFile) -> str:
        """Get decoded content of a file"""
        try:
            content = file.decoded_content.decode('utf-8')
            return content
        except Exception as e:
            logger.error("Failed to get file content", path=file.path, error=str(e))
            raise
    
    async def create_branch(self, repo: Repository, source_branch: str, target_branch: str) -> None:
        """Create a new branch from source branch"""
        try:
            # Get source branch reference
            source_ref = repo.get_git_ref(f"heads/{source_branch}")
            
            # Create new branch
            repo.create_git_ref(
                ref=f"refs/heads/{target_branch}",
                sha=source_ref.object.sha
            )
            
            logger.info("Created branch", target_branch=target_branch, source_branch=source_branch)
            
        except GithubException as e:
            if "Reference already exists" in str(e):
                logger.info("Branch already exists", branch=target_branch)
            else:
                logger.error("Failed to create branch", error=str(e))
                raise
    
    async def commit_files(
        self,
        repo: Repository,
        branch: str,
        files: List[Tuple[str, str]],  # (path, content) pairs
        commit_message: str
    ) -> None:
        """Commit multiple files to repository"""
        try:
            # Get the current commit SHA
            ref = repo.get_git_ref(f"heads/{branch}")
            current_sha = ref.object.sha
            
            # Create blobs for each file
            blobs = []
            for file_path, content in files:
                blob = repo.create_git_blob(content, "utf-8")
                blobs.append((file_path, blob.sha))
            
            # Get current tree
            base_tree = repo.get_git_tree(current_sha)
            
            # Create tree elements
            tree_elements = []
            for file_path, blob_sha in blobs:
                tree_elements.append({
                    "path": file_path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_sha
                })
            
            # Create new tree
            new_tree = repo.create_git_tree(tree_elements, base_tree)
            
            # Create commit
            commit = repo.create_git_commit(
                message=commit_message,
                tree=new_tree,
                parents=[repo.get_git_commit(current_sha)]
            )
            
            # Update branch reference
            ref.edit(commit.sha)
            
            logger.info("Files committed", branch=branch, file_count=len(files))
            
        except GithubException as e:
            logger.error("Failed to commit files", error=str(e))
            raise
    
    async def create_pull_request(
        self,
        repo: Repository,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main"
    ) -> str:
        """Create a pull request"""
        try:
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch
            )
            
            logger.info("Pull request created", pr_number=pr.number, pr_url=pr.html_url)
            return pr.html_url
            
        except GithubException as e:
            logger.error("Failed to create pull request", error=str(e))
            raise