from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import logging
from ..orchestration.task_manager import TaskType, Task
from ..context.context_manager import ContextManager

@dataclass
class ProjectPlan:
    components: List[str]
    dependencies: Dict[str, List[str]]
    tasks: List[Dict]
    framework_choices: Dict[str, str]
    estimated_timeline: Dict[str, int]  # in hours

class PlannerAgent:
    def __init__(self, llm_server_url: str, context_manager: ContextManager):
        self.llm_server_url = llm_server_url
        self.context_manager = context_manager
        self.logger = logging.getLogger(__name__)

    async def create_project_plan(self, project_description: str) -> ProjectPlan:
        """Create a comprehensive project plan based on the description."""
        prompt = self._create_planning_prompt(project_description)
        context = self.context_manager.get_relevant_context(project_description)
        
        # Get plan from LLM
        response = await self._query_llm(prompt, context)
        plan = self._parse_plan_response(response)
        
        return plan

    async def decompose_into_tasks(self, plan: ProjectPlan) -> List[Dict]:
        """Convert project plan into concrete tasks."""
        tasks = []
        
        # Add planning tasks
        planning_tasks = self._create_planning_tasks(plan)
        tasks.extend(planning_tasks)
        
        # Add development tasks
        dev_tasks = self._create_development_tasks(plan)
        tasks.extend(dev_tasks)
        
        # Add testing tasks
        test_tasks = self._create_testing_tasks(plan)
        tasks.extend(test_tasks)
        
        return tasks

    def _create_planning_prompt(self, description: str) -> str:
        return f"""Analyze the following project description and create a detailed development plan:

Description:
{description}

Please provide:
1. Core components needed
2. Component dependencies
3. Required frameworks and technologies
4. Implementation tasks breakdown
5. Estimated timeline for each component

Format the response as JSON with the following structure:
{{
    "components": ["component1", "component2", ...],
    "dependencies": {{"component1": ["dependency1", "dependency2"], ...}},
    "tasks": [
        {{"name": "task1", "type": "planning|development|testing", "dependencies": [], "estimate_hours": 2}},
        ...
    ],
    "framework_choices": {{"frontend": "framework1", "backend": "framework2", ...}},
    "estimated_timeline": {{"component1": 4, "component2": 6, ...}}
}}"""

    def _parse_plan_response(self, response: str) -> ProjectPlan:
        """Parse LLM response into ProjectPlan object."""
        try:
            data = json.loads(response)
            return ProjectPlan(
                components=data["components"],
                dependencies=data["dependencies"],
                tasks=data["tasks"],
                framework_choices=data["framework_choices"],
                estimated_timeline=data["estimated_timeline"]
            )
        except Exception as e:
            self.logger.error(f"Error parsing plan response: {str(e)}")
            raise

    def _create_planning_tasks(self, plan: ProjectPlan) -> List[Dict]:
        """Create initial planning and setup tasks."""
        return [
            {
                "type": TaskType.PLANNING,
                "description": "Initialize project structure",
                "dependencies": []
            },
            {
                "type": TaskType.PLANNING,
                "description": "Setup development environment",
                "dependencies": []
            },
            {
                "type": TaskType.PLANNING,
                "description": "Configure CI/CD pipeline",
                "dependencies": []
            }
        ]

    def _create_development_tasks(self, plan: ProjectPlan) -> List[Dict]:
        """Create development tasks from plan components."""
        tasks = []
        for component in plan.components:
            tasks.append({
                "type": TaskType.DEVELOPMENT,
                "description": f"Implement {component}",
                "dependencies": [
                    dep for dep in plan.dependencies.get(component, [])
                ]
            })
        return tasks

    def _create_testing_tasks(self, plan: ProjectPlan) -> List[Dict]:
        """Create testing tasks for each component."""
        return [
            {
                "type": TaskType.TESTING,
                "description": f"Test {component}",
                "dependencies": [f"Implement {component}"]
            }
            for component in plan.components
        ]

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