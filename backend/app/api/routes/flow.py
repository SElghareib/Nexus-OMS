"""
API routes for React Flow visualization.
Provides endpoints for retrieving execution graphs.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.models.audit_models import ExecutionTrace, ExecutionStatus
from app.schemas.agent_schemas import FlowData

router = APIRouter(prefix="/api/v1/flow", tags=["flow"])


@router.get("/{task_id}", response_model=FlowData)
async def get_task_flow(task_id: str, db: AsyncSession = Depends(get_db)):
    """Get flow visualization data for a specific task."""
    result = await db.execute(
        select(ExecutionTrace).where(ExecutionTrace.task_id == task_id)
    )
    trace = result.scalar_one_or_none()
    
    if not trace:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return FlowData(
        nodes=trace.nodes,
        edges=trace.edges,
        task_id=task_id,
        status=trace.status.value,
    )


@router.get("/recent", response_model=List[FlowData])
async def get_recent_flows(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Get flow data for recent tasks."""
    result = await db.execute(
        select(ExecutionTrace)
        .order_by(ExecutionTrace.started_at.desc())
        .limit(limit)
    )
    traces = result.scalars().all()
    
    return [
        FlowData(
            nodes=trace.nodes,
            edges=trace.edges,
            task_id=trace.task_id,
            status=trace.status.value,
        )
        for trace in traces
    ]
