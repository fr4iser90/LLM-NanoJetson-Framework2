from typing import Dict, List, Optional
from pathlib import Path
import logging
import aiohttp
from ..context.context_manager import ContextManager
from ..templates.template_manager import TemplateManager

class DeveloperAgent:
    def __init__(self, 
                 llm_server_url: str,
                 context_manager: ContextManager,
                 template_manager: TemplateManager):
        self.llm_server_url = llm_server_url
        self.context_manager = context_manager
        self.template_manager = template_manager
        self.logger = logging.getLogger(__name__)

    async def generate_component(self, 
                               component_name: str, 
                               description: str,
                               framework: str) -> Dict[str, str]:
        """Generate code for a component."""
        # Get relevant context
        context = self.context_manager.get_relevant_context(description)
        
        # Get appropriate template
        template = self.template_manager.get_template(component_name, framework)
        
        # Create detailed prompt
        prompt = self._create_component_prompt(
            component_name,
            description,
            framework,
            template
        )
        
        # Generate code
        code = await self._query_llm(prompt, context)
        
        # Parse and validate generated code
        files = self._parse_generated_code(code)
        
        # Validate the generated code
        self._validate_code(files)
        
        return files

    async def refactor_code(self, 
                           file_path: str, 
                           description: str) -> str:
        """Refactor existing code based on description."""
        # Load existing code
        code = Path(file_path).read_text()
        
        # Get relevant context
        context = self.context_manager.get_relevant_context(description)
        
        # Create refactoring prompt
        prompt = self._create_refactor_prompt(code, description)
        
        # Generate refactored code
        refactored_code = await self._query_llm(prompt, context)
        
        # Validate the refactored code
        self._validate_code({"refactored.py": refactored_code})
        
        return refactored_code

    def _create_component_prompt(self, 
                               name: str, 
                               description: str,
                               framework: str,
                               template: Optional[str]) -> str:
        prompt = f"""Generate code for the following component:

Name: {name}
Description: {description}
Framework: {framework}

Requirements:
1. Follow Python best practices and PEP 8
2. Include comprehensive docstrings
3. Add type hints
4. Include error handling
5. Make code testable
6. Add necessary comments

"""
        if template:
            prompt += f"\nUse the following template as a base:\n{template}\n"
            
        return prompt

    def _create_refactor_prompt(self, code: str, description: str) -> str:
        return f"""Refactor the following code according to the description:

Description: {description}

Original Code:
{code}

Requirements:
1. Maintain functionality
2. Improve code quality
3. Add missing error handling
4. Improve performance where possible
5. Add or improve documentation
"""

    def _parse_generated_code(self, code: str) -> Dict[str, str]:
        """Parse generated code into individual files."""
        # Simple parsing for now - assume single file
        return {"component.py": code}

    def _validate_code(self, files: Dict[str, str]):
        """Validate generated code for common issues."""
        for filename, code in files.items():
            try:
                # Basic syntax check
                compile(code, filename, 'exec')
                
                # TODO: Add more validation
                # - Style checking
                # - Security scanning
                # - Complexity analysis
                
            except Exception as e:
                self.logger.error(f"Code validation failed for {filename}: {str(e)}")
                raise

    async def _query_llm(self, prompt: str, context: List[Dict] = None) -> str:
        """Send query to LLM server and get response."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.llm_server_url}/generate",
                json={
                    "prompt": prompt,
                    "context_chunks": context,
                    "max_tokens": 2048,
                    "temperature": 0.7
                }
            ) as response:
                if response.status != 200:
                    raise Exception(f"LLM query failed: {await response.text()}")
                result = await response.json()
                return result["generated_code"] 