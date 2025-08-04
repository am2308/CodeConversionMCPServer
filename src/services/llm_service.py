"""
LLM service for shell script to Python conversion
"""
import asyncio
from typing import Optional
import structlog
import openai
from openai import OpenAI

logger = structlog.get_logger()

class LLMService:
    """Service for LLM operations"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    async def health_check(self) -> bool:
        """Check LLM service health"""
        try:
            # Test API access with a simple request
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.error("LLM health check failed", error=str(e))
            return False
    
    async def convert_shell_to_python(
        self,
        shell_content: str,
        file_path: str,
        context: Optional[str] = None
    ) -> tuple[str, str]:
        """Convert shell script to Python code"""
        
        system_prompt = """
You are an expert in converting shell scripts to Python code. Your task is to:

1. Analyze the shell script and understand its functionality
2. Convert it to equivalent Python code that maintains the same behavior
3. Use appropriate Python libraries (subprocess, os, pathlib, etc.)
4. Add proper error handling and logging
5. Include docstrings and comments explaining the conversion
6. Ensure the Python code is production-ready and follows best practices

Guidelines:
- Use subprocess.run() for executing external commands
- Use pathlib for file operations
- Add proper exception handling
- Include type hints where appropriate
- Use logging instead of echo statements
- Maintain the original script's functionality exactly
"""

        user_prompt = f"""
Convert the following shell script to Python:

File: {file_path}
{f"Context: {context}" if context else ""}

Shell Script:
```bash
{shell_content}
```

Please provide:
1. The converted Python code
2. A brief explanation of key conversion decisions
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            # Split response into code and explanation
            if "```python" in content:
                parts = content.split("```python")
                if len(parts) > 1:
                    code_part = parts[1].split("```")[0].strip()
                    explanation = content.replace(f"```python{code_part}```", "").strip()
                else:
                    code_part = content
                    explanation = "Conversion completed"
            else:
                code_part = content
                explanation = "Conversion completed"
            
            logger.info("Shell script converted", file_path=file_path)
            return code_part, explanation
            
        except Exception as e:
            logger.error("Failed to convert shell script", file_path=file_path, error=str(e))
            raise
    
    async def generate_pr_description(
        self,
        conversions: list,
        repo_name: str
    ) -> str:
        """Generate pull request description"""
        
        conversion_summary = "\n".join([
            f"- `{conv['original_path']}` → `{conv['converted_path']}`"
            for conv in conversions
        ])
        
        prompt = f"""
Generate a comprehensive pull request description for converting shell scripts to Python in the repository '{repo_name}'.

Conversions made:
{conversion_summary}

The PR description should include:
1. Clear title summarizing the changes
2. Overview of what was converted
3. Benefits of the conversion
4. Any breaking changes or considerations
5. Testing recommendations

Keep it professional and informative.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error("Failed to generate PR description", error=str(e))
            return f"Automated conversion of shell scripts to Python in {repo_name}"