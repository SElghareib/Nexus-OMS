"""
API routes for Agent integration.
Handles task execution and flow visualization.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.db.session import get_db
from app.schemas.agent_schemas import (
    AgentTaskRequest, 
    AgentTaskResponse,
    FlowData,
)
from app.services.agent_client import agent_client, AgentClientError
from app.services.flow_engine import create_flow_engine
from app.models.audit_models import ExecutionTrace, ExecutionStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


@router.post("/run", response_model=AgentTaskResponse)
async def run_agent_task(
    request: AgentTaskRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Run an agent task.
    
    1. Sends the task to Agent Core (Project 1) to get an execution plan
    2. Executes the plan using local OMS tools
    3. Returns the result with execution trace for visualization
    """
    try:
        # Get plan from Agent Core
        logger.info(f"Sending task to Agent Core: {request.task_description}")
        plan_response = await agent_client.send_task(request)
        
        if not plan_response.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent Core failed to generate plan: {plan_response.reasoning}"
            )
        
        logger.info(f"Received plan with {len(plan_response.plan)} steps")
        
        # Execute the plan
        engine = create_flow_engine(db)
        result = await engine.execute_plan(
            user_request=request.task_description,
            plan=plan_response.plan,
            reasoning=plan_response.reasoning,
        )
        
        return AgentTaskResponse(**result)
        
    except AgentClientError as e:
        logger.error(f"Agent Core communication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error executing agent task: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute task: {str(e)}",
        )


@router.get("/flow/{task_id}", response_model=FlowData)
async def get_flow_data(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get React Flow visualization data for a completed or running task.
    """
    result = await db.execute(
        select(ExecutionTrace).where(ExecutionTrace.task_id == task_id)
    )
    trace = result.scalar_one_or_none()
    
    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    return FlowData(
        nodes=trace.nodes,
        edges=trace.edges,
        task_id=task_id,
        status=trace.status.value,
    )


@router.get("/health")
async def agent_health():
    """Check if Agent Core is available."""
    is_healthy = await agent_client.health_check()
    
    if is_healthy:
        return {"status": "healthy", "agent_core": "connected"}
    else:
        return {"status": "degraded", "agent_core": "disconnected"}
