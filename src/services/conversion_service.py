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
from ..config import settings

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
        source_languages: List[str] = None,
        target_language: str = "python",
        task_id: str = None
    ) -> None:
        """Process entire repository for code conversion"""
        
        if not target_branch:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            target_branch = f"convert-to-{target_language}-{timestamp}"
        
        try:
            logger.info(
                "Starting repository processing",
                repo_owner=repo_owner,
                repo_name=repo_name,
                source_branch=source_branch,
                target_branch=target_branch,
                source_languages=source_languages,
                target_language=target_language,
                task_id=task_id
            )
            
            # Get repository
            repo = await self.github_service.get_repository(repo_owner, repo_name)
            
            # Find convertible files
            convertible_files = await self.github_service.find_convertible_files(
                repo, source_branch, source_languages
            )
            
            if not convertible_files:
                logger.info("No convertible files found in repository")
                return
            
            # Create target branch
            await self.github_service.create_branch(repo, source_branch, target_branch)
            
            # Process each convertible file
            conversions = []
            files_to_commit = []
            
            for file_content, source_language in convertible_files:
                try:
                    logger.info("Processing file", 
                              path=file_content.path, 
                              language=source_language)
                    
                    # Get file content
                    source_content = await self.github_service.get_file_content(file_content)
                    
                    # Convert to target language
                    converted_code, conversion_notes = await self.llm_service.convert_code_to_python(
                        source_content,
                        file_content.path,
                        source_language,
                        target_language
                    )
                    
                    # Determine target file path
                    target_path = self._get_target_path(file_content.path, target_language)
                    
                    # Add proper formatting
                    formatted_code = self._format_target_code(
                        converted_code, 
                        file_content.path, 
                        source_language,
                        target_language
                    )
                    
                    # Track conversion
                    conversion = FileConversion(
                        original_path=file_content.path,
                        converted_path=target_path,
                        original_content=source_content,
                        converted_content=formatted_code,
                        source_language=source_language,
                        target_language=target_language,
                        conversion_notes=conversion_notes
                    )
                    
                    conversions.append(conversion)
                    files_to_commit.append((target_path, formatted_code))
                    
                    logger.info("File converted successfully", 
                              original=file_content.path, 
                              converted=target_path,
                              source_language=source_language,
                              target_language=target_language)
                    
                except Exception as e:
                    logger.error("Failed to process file", 
                                path=file_content.path, 
                                language=source_language,
                                error=str(e))
                    continue
            
            if not files_to_commit:
                logger.warning("No files were successfully converted")
                return
            
            # Commit all converted files
            languages_summary = {}
            for conv in conversions:
                lang = conv.source_language
                languages_summary[lang] = languages_summary.get(lang, 0) + 1
            
            lang_summary_text = ", ".join([f"{count} {lang}" for lang, count in languages_summary.items()])
            
            commit_message = f"Convert multiple languages to {target_language}\n\nConverted {len(files_to_commit)} files ({lang_summary_text}) to {target_language} equivalents.\n\nFiles converted:\n" + "\n".join([f"- {conv.original_path} ({conv.source_language}) → {conv.converted_path}" for conv in conversions])
            
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
            pr_title = f"Convert multiple languages to {target_language} ({len(conversions)} files)"
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
                languages_converted=list(languages_summary.keys()),
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
    
    def _get_target_path(self, original_path: str, target_language: str) -> str:
        """Convert original file path to target language file path"""
        # Get file extension for target language
        target_extensions = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "go": ".go",
            "rust": ".rs",
            "java": ".java"
        }
        
        target_ext = target_extensions.get(target_language, ".py")
        
        # Remove original extension and add target extension
        for ext in settings.supported_extensions.keys():
            if original_path.endswith(ext):
                return original_path[:-len(ext)] + target_ext
        
        # If no known extension, just append target extension
        return original_path + target_ext
    
    def _format_target_code(
        self, 
        converted_code: str, 
        original_path: str, 
        source_language: str,
        target_language: str
    ) -> str:
        """Format target code with proper headers and structure"""
        
        if target_language != "python":
            return converted_code
            
        # Python-specific formatting
        header = f'''#!/usr/bin/env python3
"""
Converted from {source_language}: {original_path}
Generated by MCP Multi-Language to Python Converter
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

'''
        
        # Ensure the code is properly indented if it's meant to be in a main function
        if 'def main():' not in converted_code and 'if __name__ == "__main__":' not in converted_code:
            main_function = '''
def main():
    """Main function converted from ''' + source_language + '''"""
    try:
''' + '\n'.join(f'        {line}' for line in converted_code.split('\n')) + '''
    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
            return header + main_function
        else: