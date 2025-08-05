"""
LLM service for multi-language to Python conversion
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
    
    async def convert_code_to_python(
        self,
        source_content: str,
        file_path: str,
        source_language: str,
        target_language: str = "python",
        context: Optional[str] = None
    ) -> tuple[str, str]:
        """Convert source code to Python"""
        
        # Language-specific conversion instructions
        language_instructions = {
            "shell": "shell scripts using subprocess, os, and pathlib libraries",
            "powershell": "PowerShell scripts using subprocess and appropriate Python libraries",
            "typescript": "TypeScript code to Python, maintaining type safety where possible",
            "javascript": "JavaScript code to Python, adapting async patterns appropriately",
            "go": "Go code to Python, adapting goroutines to asyncio where applicable",
            "rust": "Rust code to Python, maintaining memory safety concepts where relevant",
            "ruby": "Ruby code to Python, adapting Ruby idioms to Pythonic patterns",
            "php": "PHP code to Python, adapting web-specific patterns appropriately",
            "java": "Java code to Python, simplifying object-oriented patterns where beneficial",
            "scala": "Scala code to Python, adapting functional programming concepts",
            "kotlin": "Kotlin code to Python, maintaining null safety concepts where possible",
            "swift": "Swift code to Python, adapting iOS/macOS patterns to cross-platform equivalents",
            "csharp": "C# code to Python, adapting .NET patterns to Python equivalents",
            "cpp": "C++ code to Python, using appropriate libraries for performance-critical sections",
            "c": "C code to Python, using ctypes or appropriate libraries for system calls",
            "perl": "Perl code to Python, adapting regex and text processing patterns",
            "r": "R code to Python using pandas, numpy, and matplotlib for data analysis",
            "lua": "Lua code to Python, adapting embedded scripting patterns",
            "dart": "Dart code to Python, adapting Flutter/web patterns appropriately",
            "groovy": "Groovy code to Python, adapting build automation and scripting patterns"
        }
        
        conversion_instruction = language_instructions.get(
            source_language, 
            f"{source_language} code to Python"
        )
        
        system_prompt = f"""
You are an expert in converting {source_language} code to {target_language}. Your task is to:

1. Analyze the {source_language} code and understand its functionality
2. Convert it to equivalent {target_language} code that maintains the same behavior
3. Use appropriate Python libraries and best practices
4. Add proper error handling and logging
5. Include docstrings and comments explaining the conversion
6. Ensure the {target_language} code is production-ready and follows best practices
7. Maintain the original logic flow and functionality
8. Adapt language-specific patterns to Pythonic equivalents

Focus on converting {conversion_instruction}.
Guidelines:
- Use appropriate Python libraries for the source language's functionality
- For shell scripts: Use subprocess.run() for external commands
- For web languages: Use Flask/FastAPI for web functionality
- For data languages: Use pandas/numpy for data processing
- For system languages: Use appropriate system libraries
- Use pathlib for file operations
- Add proper exception handling
- Include type hints where appropriate
- Use logging instead of print/echo statements
- Maintain the original script's functionality exactly
- Add comprehensive docstrings explaining the conversion
"""

        user_prompt = f"""
Convert the following {source_language} code to {target_language}:

File: {file_path}
{f"Context: {context}" if context else ""}

{source_language.title()} Code:
```{source_language}
{source_content}
```

Please provide:
1. The converted {target_language} code
2. A brief explanation of key conversion decisions
3. Any important notes about functionality changes or limitations
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=3000
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
            
            logger.info("Code converted", 
                       file_path=file_path, 
                       source_language=source_language,
                       target_language=target_language)
            return code_part, explanation
            
        except Exception as e:
            logger.error("Failed to convert code", 
                        file_path=file_path, 
                        source_language=source_language,
                        error=str(e))
            raise
    
    async def generate_pr_description(
        self,
        conversions: list,
        repo_name: str
    ) -> str:
        """Generate pull request description"""
        
        conversion_summary = "\n".join([
            f"- `{conv['original_path']}` ({conv['source_language']}) → `{conv['converted_path']}` ({conv['target_language']})"
            for conv in conversions
        ])
        
        languages_converted = list(set([conv['source_language'] for conv in conversions]))
        
        prompt = f"""
Generate a comprehensive pull request description for converting multiple programming languages to Python in the repository '{repo_name}'.

Languages converted: {', '.join(languages_converted)}
Conversions made:
{conversion_summary}

The PR description should include:
1. Clear title summarizing the changes
2. Overview of what was converted
3. Benefits of standardizing on Python
4. Any breaking changes or considerations
5. Testing recommendations
6. Migration notes for different language types

Keep it professional and informative.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error("Failed to generate PR description", error=str(e))