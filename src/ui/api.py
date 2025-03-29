from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
import logging
from ..agents.planner import PlannerAgent
from ..agents.developer import DeveloperAgent
from ..agents.tester import TestingAgent
from ..orchestration.task_manager import TaskManager
from ..context.context_manager import ContextManager
from ..templates.template_manager import TemplateManager

app = FastAPI(title="AutoCoder UI API")
logger = logging.getLogger(__name__)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ProjectRequest(BaseModel):
    name: str
    description: str
    framework: str
    template: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    type: str
    status: str
    description: str
    progress: float
    result: Optional[Dict] = None

class ProjectStatus(BaseModel):
    name: str
    status: str
    tasks: List[TaskResponse]
    current_file: Optional[str] = None
    progress: float

# Initialize components
context_manager = ContextManager()
template_manager = TemplateManager(Path("templates"))
task_manager = TaskManager()

# Initialize agents
planner_agent = PlannerAgent("http://localhost:8080", context_manager)
developer_agent = DeveloperAgent("http://localhost:8080", context_manager, template_manager)
testing_agent = TestingAgent("http://localhost:8080", context_manager)

@app.post("/projects", response_model=ProjectStatus)
async def create_project(request: ProjectRequest):
    """Create a new project and start the development process."""
    try:
        # Create project plan
        plan = await planner_agent.create_project_plan(request.description)
        
        # Convert plan to tasks
        tasks = await planner_agent.decompose_into_tasks(plan)
        
        # Register tasks with task manager
        task_ids = []
        for task in tasks:
            task_id = task_manager.create_task(
                type=task["type"],
                description=task["description"],
                dependencies=task.get("dependencies", [])
            )
            task_ids.append(task_id)
        
        # Start task execution
        asyncio.create_task(task_manager.execute_all())
        
        return ProjectStatus(
            name=request.name,
            status="started",
            tasks=[],
            progress=0.0
        )
        
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_name}/status", response_model=ProjectStatus)
async def get_project_status(project_name: str):
    """Get current project status."""
    try:
        tasks = task_manager.get_all_tasks()
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task.status == "completed")
        
        return ProjectStatus(
            name=project_name,
            status="in_progress" if completed_tasks < total_tasks else "completed",
            tasks=[
                TaskResponse(
                    id=str(task.id),
                    type=task.type.value,
                    status=task.status.value,
                    description=task.description,
                    progress=1.0 if task.status == "completed" else 0.0,
                    result=task.result
                )
                for task in tasks
            ],
            progress=completed_tasks / total_tasks if total_tasks > 0 else 0.0
        )
        
    except Exception as e:
        logger.error(f"Error getting project status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/projects/{project_name}/events")
async def project_events(websocket: WebSocket, project_name: str):
    """WebSocket endpoint for real-time project updates."""
    await websocket.accept()
    try:
        while True:
            # Get current status
            status = await get_project_status(project_name)
            
            # Send update
            await websocket.send_json(status.dict())
            
            # Wait before next update
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 