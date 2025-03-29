from pathlib import Path
from typing import Dict, List, Optional
import asyncio
import aiohttp
import logging
from pydantic import BaseModel

class ProjectConfig(BaseModel):
    name: str
    description: str
    framework: str
    dependencies: List[str]
    structure: Dict[str, str]

class ProjectOrchestrator:
    def __init__(self, llm_server_url: str):
        self.llm_server_url = llm_server_url
        self.logger = logging.getLogger(__name__)
        
    async def initialize_project(self, config: ProjectConfig) -> Path:
        """Initialize a new project with the given configuration."""
        project_path = Path(f"projects/{config.name}")
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Generate project structure
        await self._generate_structure(project_path, config)
        
        # Generate initial files
        await self._generate_core_files(project_path, config)
        
        return project_path
    
    async def _generate_structure(self, path: Path, config: ProjectConfig):
        """Create the project directory structure."""
        for dir_path, description in config.structure.items():
            (path / dir_path).mkdir(parents=True, exist_ok=True)
            # Create README for each directory
            readme = path / dir_path / "README.md"
            readme.write_text(description)
    
    async def _generate_core_files(self, path: Path, config: ProjectConfig):
        """Generate core project files using the LLM."""
        core_files = {
            "requirements.txt": self._generate_requirements_prompt(config),
            "README.md": self._generate_readme_prompt(config),
            "main.py": self._generate_main_prompt(config),
        }
        
        async with aiohttp.ClientSession() as session:
            for filename, prompt in core_files.items():
                try:
                    content = await self._generate_file_content(session, prompt)
                    (path / filename).write_text(content)
                except Exception as e:
                    self.logger.error(f"Error generating {filename}: {str(e)}")
    
    def _generate_requirements_prompt(self, config: ProjectConfig) -> str:
        return f"""Generate a requirements.txt file for a {config.framework} project with the following dependencies:
        {', '.join(config.dependencies)}
        Include version numbers and ensure compatibility."""
    
    def _generate_readme_prompt(self, config: ProjectConfig) -> str:
        return f"""Create a README.md file for project {config.name}
        Description: {config.description}
        Framework: {config.framework}
        Include sections for setup, usage, and development."""
    
    def _generate_main_prompt(self, config: ProjectConfig) -> str:
        return f"""Create the main.py file for a {config.framework} project.
        Project description: {config.description}
        Include proper imports, configuration, and a basic application setup."""
    
    async def _generate_file_content(self, session: aiohttp.ClientSession, prompt: str) -> str:
        """Generate file content using the LLM server."""
        async with session.post(
            f"{self.llm_server_url}/generate",
            json={"prompt": prompt, "max_tokens": 1024}
        ) as response:
            if response.status != 200:
                raise Exception(f"LLM server error: {await response.text()}")
            result = await response.json()
            return result["generated_code"]

# Usage example
async def main():
    orchestrator = ProjectOrchestrator("http://localhost:8080")
    config = ProjectConfig(
        name="sample_project",
        description="A sample FastAPI backend project",
        framework="fastapi",
        dependencies=["fastapi", "uvicorn", "sqlalchemy"],
        structure={
            "src": "Source code directory",
            "src/api": "API endpoints",
            "src/models": "Data models",
            "src/services": "Business logic",
            "tests": "Test files",
        }
    )
    
    project_path = await orchestrator.initialize_project(config)
    print(f"Project initialized at {project_path}")

if __name__ == "__main__":
    asyncio.run(main()) 