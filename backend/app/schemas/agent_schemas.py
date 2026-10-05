"""
Pydantic schemas for Agent communication and Flow visualization.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# Agent Schemas
class AgentTaskRequest(BaseModel):
    """Request to run an agent task."""
    task_description: str = Field(..., description="Natural language description of the task")
    order_id: Optional[int] = Field(None, description="Optional order ID context")
    customer_id: Optional[int] = Field(None, description="Optional customer ID context")
    require_approval: bool = Field(True, description="Whether high-risk actions require approval")


class AgentPlanStep(BaseModel):
    """A single step in the agent's plan."""
    step_number: int
    tool_name: str
    description: str
    parameters: Dict[str, Any]
    permission_level: str  # read, low_risk_write, high_risk_write


class AgentPlanResponse(BaseModel):
    """Response from Agent Core with the execution plan."""
    success: bool
    plan: List[AgentPlanStep]
    reasoning: str
    estimated_steps: int


class AgentTaskResponse(BaseModel):
    """Response after executing an agent task."""
    task_id: str
    success: bool
    result: Any
    execution_trace: Dict[str, Any]
    message: str
    requires_approval: bool = False
    pending_actions: List[Dict[str, Any]] = []


# Flow Schemas (for React Flow visualization)
class FlowNode(BaseModel):
    """A node in the execution flow graph."""
    id: str
    type: str  # plan, tool, result
    label: str
    status: str  # pending, running, success, failed, waiting_approval
    data: Dict[str, Any]
    position: Dict[str, float]


class FlowEdge(BaseModel):
    """An edge connecting nodes in the flow graph."""
    id: str
    source: str
    target: str
    label: Optional[str] = None
    animated: bool = False
    style: Optional[Dict[str, Any]] = None


class FlowData(BaseModel):
    """Complete flow data for React Flow."""
    nodes: List[FlowNode]
    edges: List[FlowEdge]
    task_id: str
    status: str
