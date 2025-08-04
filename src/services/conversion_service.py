"""
Main conversion service orchestrating the entire process
"""
import asyncio
from typing import List
from datetime import datetime
import structlog

from .github_service import GitHubService
from .llm_service import LLMService
from ..models.schemas import FileConversion

logger = structlog.get_logger()

class ConversionService:
    """Service orchestrating the conversion process"""
    
    def __init__(self, github_service: GitHubService, llm_service: LLMService):
        self.github_service = github_service
        self.llm_service = llm_service
    
    async def process_repository(
        self,
        repo_owner: str,
        repo_name: str,
        source_branch: str = "main",
        target_branch: str = None,
        task_id: str = None
    ) -> None:
        """Process entire repository for shell script conversion"""
        
        if not target_branch:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            target_branch = f"convert-shell-to-python-{timestamp}"
        
        try:
            logger.info(
                "Starting repository processing",
                repo_owner=repo_owner,
                repo_name=repo_name,
                source_branch=source_branch,
                target_branch=target_branch,
                task_id=task_id
            )
            
            # Get repository
            repo = await self.github_service.get_repository(repo_owner, repo_name)
            
            # Find shell files
            shell_files = await self.github_service.find_shell_files(repo, source_branch)
            
            if not shell_files:
                logger.info("No shell files found in repository")
                return
            
            # Create target branch
            await self.github_service.create_branch(repo, source_branch, target_branch)
            
            # Process each shell file
            conversions = []
            files_to_commit = []
            
            for shell_file in shell_files:
                try:
                    logger.info("Processing file", path=shell_file.path)
                    
                    # Get file content
                    shell_content = await self.github_service.get_file_content(shell_file)
                    
                    # Convert to Python
                    python_code, conversion_notes = await self.llm_service.convert_shell_to_python(
                        shell_content,
                        shell_file.path
                    )
                    
                    # Determine Python file path
                    python_path = self._get_python_path(shell_file.path)
                    
                    # Add Python shebang and proper formatting
                    formatted_python_code = self._format_python_code(python_code, shell_file.path)
                    
                    # Track conversion
                    conversion = FileConversion(
                        original_path=shell_file.path,
                        converted_path=python_path,
                        original_content=shell_content,
                        converted_content=formatted_python_code,
                        conversion_notes=conversion_notes
                    )
                    
                    conversions.append(conversion)
                    files_to_commit.append((python_path, formatted_python_code))
                    
                    logger.info("File converted successfully", 
                              original=shell_file.path, 
                              converted=python_path)
                    
                except Exception as e:
                    logger.error("Failed to process file", path=shell_file.path, error=str(e))
                    continue
            
            if not files_to_commit:
                logger.warning("No files were successfully converted")
                return
            
            # Commit all converted files
            commit_message = f"Convert shell scripts to Python\n\nConverted {len(files_to_commit)} shell scripts to Python equivalents.\n\nFiles converted:\n" + "\n".join([f"- {conv.original_path} → {conv.converted_path}" for conv in conversions])
            
            await self.github_service.commit_files(
                repo,
                target_branch,
                files_to_commit,
                commit_message
            )
            
            # Generate PR description
            pr_body = await self.llm_service.generate_pr_description(
                [conv.dict() for conv in conversions],
                repo_name
            )
            
            # Create pull request
            pr_title = f"Convert shell scripts to Python ({len(conversions)} files)"
            pr_url = await self.github_service.create_pull_request(
                repo,
                pr_title,
                pr_body,
                target_branch,
                source_branch
            )
            
            logger.info(
                "Repository processing completed",
                conversions_count=len(conversions),
                pr_url=pr_url,
                task_id=task_id
            )
            
        except Exception as e:
            logger.error("Repository processing failed", 
                        repo_owner=repo_owner, 
                        repo_name=repo_name,
                        error=str(e),
                        task_id=task_id)
            raise
    
    def _get_python_path(self, shell_path: str) -> str:
        """Convert shell file path to Python file path"""
        # Remove .sh extension and add .py
        if shell_path.endswith('.sh'):
            return shell_path[:-3] + '.py'
        elif shell_path.endswith('.bash'):
            return shell_path[:-5] + '.py'
        else:
            return shell_path + '.py'
    
    def _format_python_code(self, python_code: str, original_path: str) -> str:
        """Format Python code with proper headers and structure"""
        header = f'''#!/usr/bin/env python3
"""
Converted from shell script: {original_path}
Generated by MCP GitHub Shell to Python Converter
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

'''
        
        # Ensure the code is properly indented if it's meant to be in a main function
        if 'def main():' not in python_code and 'if __name__ == "__main__":' not in python_code:
            main_function = '''
def main():
    """Main function converted from shell script"""
    try:
''' + '\n'.join(f'        {line}' for line in python_code.split('\n')) + '''
    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
            return header + main_function
        else:
            return header + python_code