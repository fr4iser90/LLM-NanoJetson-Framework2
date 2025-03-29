from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
import aiohttp
import logging
import yaml
from pathlib import Path
from ..agents.planner import PlannerAgent
from ..agents.developer import DeveloperAgent
from ..agents.tester import TestingAgent
from ..orchestration.task_manager import TaskManager
from ..context.context_manager import ContextManager
from ..templates.template_manager import TemplateManager
import os
import json

# Konfiguration direkt laden
config_path = Path("/app/config/config.yml")  # Direkt den gemounteten Pfad verwenden
with open(config_path) as f:
    config = yaml.safe_load(f)

app = FastAPI(title="AutoCoder UI API")
logger = logging.getLogger(__name__)

# CORS konfigurieren
origins = json.loads(os.getenv('CORS_ORIGINS', '["http://localhost:3333"]'))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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

# Get configuration from config.yml
MAIN_PC_HOST = config['main_pc']['host']
MAIN_PC_API_PORT = config['main_pc']['api_port']
JETSON_HOST = config['jetson']['host']
JETSON_LLM_PORT = config['jetson']['llm_port']

# Use configuration
LLM_SERVER_URL = f"http://{JETSON_HOST}:{JETSON_LLM_PORT}"

# Initialize components
context_manager = ContextManager()
template_manager = TemplateManager(Path("templates"))
task_manager = TaskManager()

# Initialize agents
planner_agent = PlannerAgent(LLM_SERVER_URL, context_manager)
developer_agent = DeveloperAgent(LLM_SERVER_URL, context_manager, template_manager)
testing_agent = TestingAgent(LLM_SERVER_URL, context_manager)

@app.get("/")
async def root():
    """Root endpoint that returns API information."""
    return {
        "name": "AutoCoder API",
        "version": "1.0.0",
        "endpoints": [
            "/projects",
            "/projects/{project_name}/status",
            "/ws/projects/{project_name}/events"
        ]
    }

@app.post("/projects", response_model=ProjectStatus)
async def create_project(request: ProjectRequest):
    """Create a new project and start the development process."""
    try:
        # Erstelle eine neue aiohttp Session für jeden Request
        async with aiohttp.ClientSession() as session:
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
            
            # Start task execution in background
            asyncio.create_task(task_manager.execute_all())
            
            return ProjectStatus(
                name=request.name,
                status="started",
                tasks=[],
                progress=0.0
            )
            
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        logger.exception(e)  # Log full traceback
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