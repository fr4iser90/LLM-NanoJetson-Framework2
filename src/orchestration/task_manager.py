from typing import List, Dict, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging
from uuid import UUID, uuid4

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskType(Enum):
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    REFACTORING = "refactoring"

@dataclass
class Task:
    id: UUID
    type: TaskType
    description: str
    dependencies: List[UUID]
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None
    error: Optional[str] = None

class TaskManager:
    def __init__(self):
        self.tasks: Dict[UUID, Task] = {}
        self.handlers: Dict[TaskType, Callable] = {}
        self.logger = logging.getLogger(__name__)
        
    def register_handler(self, task_type: TaskType, handler: Callable):
        """Register a handler function for a specific task type."""
        self.handlers[task_type] = handler
        
    def create_task(self, 
                   type: TaskType, 
                   description: str, 
                   dependencies: List[UUID] = None) -> UUID:
        """Create a new task and return its ID."""
        task_id = uuid4()
        self.tasks[task_id] = Task(
            id=task_id,
            type=type,
            description=description,
            dependencies=dependencies or [],
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        return task_id
        
    async def execute_task(self, task_id: UUID):
        """Execute a single task."""
        task = self.tasks[task_id]
        
        # Check dependencies
        for dep_id in task.dependencies:
            dep_task = self.tasks[dep_id]
            if dep_task.status != TaskStatus.COMPLETED:
                raise ValueError(f"Dependency {dep_id} not completed")
        
        # Update status and start time
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        try:
            # Get and execute handler
            handler = self.handlers.get(task.type)
            if not handler:
                raise ValueError(f"No handler registered for task type {task.type}")
            
            result = await handler(task)
            
            # Update task on success
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            
        except Exception as e:
            # Update task on failure
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self.logger.error(f"Task {task_id} failed: {str(e)}")
            raise
        
    async def execute_all(self):
        """Execute all pending tasks in dependency order."""
        while True:
            # Find executable tasks (all dependencies completed)
            executable = [
                task_id for task_id, task in self.tasks.items()
                if task.status == TaskStatus.PENDING and
                all(self.tasks[dep].status == TaskStatus.COMPLETED 
                    for dep in task.dependencies)
            ]
            
            if not executable:
                break
                
            # Execute tasks in parallel
            await asyncio.gather(
                *(self.execute_task(task_id) for task_id in executable)
            )
            
    def get_task_status(self, task_id: UUID) -> TaskStatus:
        """Get the current status of a task."""
        return self.tasks[task_id].status
        
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks."""
        return list(self.tasks.values()) 