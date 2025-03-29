from typing import List, Dict, Optional
import ast
import asyncio
import pytest
import logging
import aiohttp
from pathlib import Path
from ..context.context_manager import ContextManager

class TestingAgent:
    def __init__(self, llm_server_url: str, context_manager: ContextManager):
        self.llm_server_url = llm_server_url
        self.context_manager = context_manager
        self.logger = logging.getLogger(__name__)

    async def generate_tests(self, 
                           file_path: str, 
                           test_description: Optional[str] = None) -> str:
        """Generate tests for a given file."""
        # Read source code
        code = Path(file_path).read_text()
        
        # Parse code to get testable elements
        testable_items = self._analyze_code(code)
        
        # Get relevant context
        context = self.context_manager.get_relevant_context(code)
        
        # Generate test code
        prompt = self._create_test_prompt(code, testable_items, test_description)
        test_code = await self._query_llm(prompt, context)
        
        return test_code

    async def run_tests(self, test_file: str) -> Dict:
        """Run tests and return results."""
        try:
            # Run pytest programmatically
            result = pytest.main(["-v", test_file])
            
            # Parse and return results
            return {
                "success": result == 0,
                "exit_code": result,
                "output": "Test results would be parsed here"
            }
        except Exception as e:
            self.logger.error(f"Error running tests: {str(e)}")
            return {
                "success": False,
                "exit_code": 1,
                "error": str(e)
            }

    def _analyze_code(self, code: str) -> Dict:
        """Analyze code to find testable elements."""
        try:
            tree = ast.parse(code)
            
            # Find classes and functions
            classes = []
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "methods": [n.name for n in node.body 
                                  if isinstance(n, ast.FunctionDef)]
                    })
                elif isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "args": [a.arg for a in node.args.args]
                    })
            
            return {
                "classes": classes,
                "functions": functions
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing code: {str(e)}")
            return {"classes": [], "functions": []}

    def _create_test_prompt(self, 
                           code: str, 
                           testable_items: Dict,
                           test_description: Optional[str]) -> str:
        prompt = f"""Generate pytest test cases for the following code:

Source Code:
{code}

Testable Items:
Classes: {', '.join(c['name'] for c in testable_items['classes'])}
Functions: {', '.join(f['name'] for f in testable_items['functions'])}

Requirements:
1. Use pytest fixtures where appropriate
2. Include both positive and negative test cases
3. Test edge cases
4. Add appropriate assertions
5. Include docstrings for test functions
"""
        if test_description:
            prompt += f"\nAdditional Testing Requirements:\n{test_description}"
            
        return prompt

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