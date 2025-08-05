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
        
        # Language-specific conversion instructions with intelligent library selection
        language_instructions = {
            "shell": "shell scripts using the most appropriate Python libraries instead of subprocess when possible",
            "powershell": "PowerShell scripts using native Python libraries rather than subprocess calls",
            "typescript": "TypeScript code to Python, maintaining type safety with proper type hints",
            "javascript": "JavaScript code to Python, using asyncio for async patterns and appropriate web frameworks",
            "go": "Go code to Python, adapting goroutines to asyncio and using concurrent.futures",
            "rust": "Rust code to Python, maintaining safety concepts with proper error handling",
            "ruby": "Ruby code to Python, adapting Ruby idioms to Pythonic patterns",
            "php": "PHP code to Python, using Flask/FastAPI for web functionality",
            "java": "Java code to Python, simplifying with Pythonic patterns and appropriate libraries",
            "scala": "Scala code to Python, adapting functional programming with functools and itertools",
            "kotlin": "Kotlin code to Python, maintaining null safety with Optional types",
            "swift": "Swift code to Python, adapting patterns to cross-platform equivalents",
            "csharp": "C# code to Python, using appropriate Python equivalents for .NET patterns",
            "cpp": "C++ code to Python, using numpy/scipy for performance-critical sections",
            "c": "C code to Python, using appropriate system libraries and ctypes when needed",
            "perl": "Perl code to Python, using re module and string processing libraries",
            "r": "R code to Python using pandas, numpy, matplotlib, and scipy for data analysis",
            "lua": "Lua code to Python, adapting scripting patterns appropriately",
            "dart": "Dart code to Python, adapting patterns with appropriate web/mobile frameworks",
            "groovy": "Groovy code to Python, using appropriate build automation libraries"
        }
        
        conversion_instruction = language_instructions.get(
            source_language, 
            f"{source_language} code to Python"
        )
        
        system_prompt = f"""
You are an expert Python developer with deep knowledge of the Python ecosystem and best practices. Your task is to intelligently convert {source_language} code to high-quality, production-ready Python code.

CRITICAL CONVERSION PRINCIPLES:

1. **INTELLIGENT LIBRARY SELECTION**: Choose the best Python library for each task, NOT just subprocess equivalents:
   - AWS CLI commands → boto3 (AWS SDK for Python)
   - Docker commands → docker-py library
   - Git commands → GitPython library
   - HTTP requests → requests or httpx library
   - Database operations → appropriate database drivers (psycopg2, pymongo, etc.)
   - File operations → pathlib and built-in file operations
   - JSON/XML processing → json/xml.etree libraries
   - System operations → os, shutil, platform modules
   - Network operations → socket, urllib, or specialized libraries

2. **CODE QUALITY & PYTHONIC PATTERNS**:
   - Use proper error handling with specific exception types
   - Implement comprehensive logging with structured logging
   - Add detailed docstrings and type hints
   - Follow PEP 8 and Python best practices
   - Use context managers for resource management
   - Implement proper async/await patterns when beneficial

3. **MAINTAINABILITY & EXTENSIBILITY**:
   - Create modular, reusable functions
   - Use configuration management (environment variables, config files)
   - Implement proper separation of concerns
   - Add comprehensive error handling and recovery
   - Include retry logic for external service calls
   - Make code easily testable and debuggable

4. **PERFORMANCE & EFFICIENCY**:
   - Use appropriate data structures (sets, deques, etc.)
   - Implement connection pooling for databases/APIs
   - Use generators for memory efficiency
   - Consider concurrent execution with asyncio or threading
   - Cache results when appropriate

5. **SECURITY & BEST PRACTICES**:
   - Never hardcode credentials (use environment variables)
   - Implement input validation and sanitization
   - Use secure communication protocols
   - Follow principle of least privilege
   - Handle sensitive data appropriately

SPECIFIC TECHNOLOGY MAPPINGS:
- AWS CLI → boto3 with proper session management and error handling
- cURL/wget → requests with session management and retries
- grep/awk/sed → Python string methods, re module, or pandas
- find → pathlib.Path.glob() or os.walk()
- tar/zip → tarfile/zipfile modules
- ps/top → psutil library
- systemctl → systemd-python or subprocess only when necessary
- Database CLIs → native Python database drivers
- Package managers → pip-tools, poetry, or subprocess when absolutely necessary

CONVERSION APPROACH:
1. Analyze the {source_language} code functionality and intent
2. Identify the best Python libraries and patterns for each operation
3. Restructure code for optimal Python architecture
4. Add comprehensive error handling and logging
5. Include proper configuration management
6. Ensure code is production-ready with monitoring capabilities

Focus on converting {conversion_instruction}.

IMPORTANT: Prioritize native Python libraries over subprocess calls. Only use subprocess when:
- No suitable Python library exists
- System-level operations require shell interaction
- Performance/compatibility requires external tools

Always explain your library choices and architectural decisions in the conversion notes.
"""

        user_prompt = f"""
Convert the following {source_language} code to {target_language} using the most appropriate Python libraries and patterns:

File: {file_path}
{f"Context: {context}" if context else ""}

{source_language.title()} Code:
```{source_language}
{source_content}
```

CONVERSION REQUIREMENTS:
1. **Smart Library Selection**: Use the best Python library for each operation (e.g., boto3 for AWS, requests for HTTP, GitPython for Git)
2. **Production Quality**: Include error handling, logging, configuration management, and retry logic
3. **Pythonic Code**: Use proper Python idioms, type hints, context managers, and PEP 8 compliance
4. **Maintainable Architecture**: Create modular, testable, and extensible code structure
5. **Security**: Use environment variables for credentials, validate inputs, handle sensitive data properly

Please provide:
1. **Converted Python Code**: High-quality, production-ready Python implementation
2. **Library Choices**: Explanation of why specific Python libraries were chosen over subprocess calls
3. **Architecture Decisions**: Key design decisions that improve maintainability and extensibility
4. **Dependencies**: List of required Python packages (for requirements.txt)
5. **Configuration**: Any environment variables or configuration needed
6. **Usage Examples**: How to run and configure the converted code

Focus on creating the BEST possible Python implementation, not just a direct translation.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=4000  # Increased for more comprehensive responses
            )
            
            content = response.choices[0].message.content
            
            # Enhanced response parsing for detailed conversion information
            if "```python" in content:
                parts = content.split("```python")
                if len(parts) > 1:
                    code_part = parts[1].split("```")[0].strip()
                    explanation = content.replace(f"```python\n{code_part}\n```", "").strip()
                else:
                    code_part = content
                    explanation = "Conversion completed with intelligent library selection"
            elif "```" in content and "python" in content.lower():
                # Handle cases where code might be in different format
                import re
                code_blocks = re.findall(r'```(?:python)?\n(.*?)\n```', content, re.DOTALL)
                if code_blocks:
                    code_part = code_blocks[0].strip()
                    explanation = re.sub(r'```(?:python)?\n.*?\n```', '', content, flags=re.DOTALL).strip()
                else:
                    code_part = content
                    explanation = "Conversion completed with intelligent library selection"
            else:
                code_part = content
                explanation = "Conversion completed with intelligent library selection"
            
            # Clean up the explanation to remove any remaining code artifacts
            explanation = explanation.replace("```", "").strip()
            if not explanation:
                explanation = "Code converted using best-practice Python libraries and patterns"
            
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
