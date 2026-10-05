"""
Flow Engine - Orchestrates execution of agent plans.
Executes tools, tracks progress, and builds execution graphs for visualization.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging
import uuid

from app.services.oms_tools import TOOL_REGISTRY, ToolError
from app.models.audit_models import AuditLog, ExecutionTrace, ActionType, ExecutionStatus
from app.schemas.agent_schemas import AgentPlanStep, FlowNode, FlowEdge, FlowData

logger = logging.getLogger(__name__)


class FlowEngine:
    """
    Executes agent plans step-by-step, tracking each action and building
    a visualization graph for the frontend.
    """
    
    def __init__(self, db: AsyncSession, task_id: str):
        self.db = db
        self.task_id = task_id
        self.nodes: List[FlowNode] = []
        self.edges: List[FlowEdge] = []
        self.results: Dict[str, Any] = {}
        self.pending_approvals: List[Dict[str, Any]] = []
    
    async def execute_plan(
        self,
        user_request: str,
        plan: List[AgentPlanStep],
        reasoning: str
    ) -> Dict[str, Any]:
        """
        Execute a complete agent plan.
        
        Args:
            user_request: Original user request
            plan: List of steps from Agent Core
            reasoning: Agent's reasoning for the plan
            
        Returns:
            Execution results with trace data
        """
        # Create initial node for the task
        self._add_node(
            node_id="start",
            node_type="plan",
            label="Task Received",
            status="success",
            data={
                "request": user_request,
                "reasoning": reasoning,
                "total_steps": len(plan),
            }
        )
        
        # Create execution trace record
        trace = ExecutionTrace(
            task_id=self.task_id,
            user_request=user_request,
            agent_plan=[step.model_dump() for step in plan],
            nodes=[],
            edges=[],
            status=ExecutionStatus.RUNNING,
        )
        self.db.add(trace)
        
        # Execute each step
        previous_node_id = "start"
        final_result = None
        has_pending_approval = False
        
        for i, step in enumerate(plan):
            step_id = f"step_{i}"
            
            try:
                # Add plan node
                self._add_node(
                    node_id=step_id,
                    node_type="plan",
                    label=f"Step {i+1}: {step.tool_name}",
                    status="running",
                    data={
                        "description": step.description,
                        "parameters": step.parameters,
                        "permission_level": step.permission_level,
                    },
                    position={"x": 250, "y": i * 100}
                )
                
                # Add edge from previous node
                self._add_edge(previous_node_id, step_id, label=f"Step {i+1}")
                
                # Check if tool exists
                tool_info = TOOL_REGISTRY.get(step.tool_name)
                if not tool_info:
                    raise ToolError(f"Unknown tool: {step.tool_name}")
                
                # Check permissions and approval requirements
                if tool_info["requires_approval"]:
                    # Add approval waiting node
                    approval_node_id = f"{step_id}_approval"
                    self._add_node(
                        node_id=approval_node_id,
                        node_type="result",
                        label="⚠️ Awaiting Approval",
                        status="waiting_approval",
                        data={
                            "tool": step.tool_name,
                            "action": step.description,
                            "parameters": step.parameters,
                        },
                        position={"x": 500, "y": i * 100}
                    )
                    self._add_edge(step_id, approval_node_id)
                    
                    # Store pending approval
                    self.pending_approvals.append({
                        "step_id": step_id,
                        "approval_node_id": approval_node_id,
                        "tool_name": step.tool_name,
                        "description": step.description,
                        "parameters": step.parameters,
                    })
                    has_pending_approval = True
                    
                    # Log audit entry
                    await self._log_audit(
                        action_type=ActionType(tool_info["permission_level"]),
                        tool_name=step.tool_name,
                        description=step.description,
                        input_data=step.parameters,
                        status=ExecutionStatus.WAITING_APPROVAL,
                        requires_approval=True,
                    )
                    
                    # Continue to next step without executing
                    previous_node_id = approval_node_id
                    continue
                
                # Execute the tool
                tool_function = tool_info["function"]
                result = await tool_function(self.db, **step.parameters)
                
                # Add success result node
                result_node_id = f"{step_id}_result"
                self._add_node(
                    node_id=result_node_id,
                    node_type="result",
                    label="✅ Success",
                    status="success",
                    data={
                        "tool": step.tool_name,
                        "result": result,
                    },
                    position={"x": 500, "y": i * 100}
                )
                self._add_edge(step_id, result_node_id)
                
                # Store result
                self.results[step_id] = result
                final_result = result
                
                # Log audit entry
                await self._log_audit(
                    action_type=ActionType(tool_info["permission_level"]),
                    tool_name=step.tool_name,
                    description=step.description,
                    input_data=step.parameters,
                    output_data=result,
                    status=ExecutionStatus.SUCCESS,
                    requires_approval=False,
                )
                
                previous_node_id = result_node_id
                
            except ToolError as e:
                logger.error(f"Tool execution failed: {e}")
                
                # Add failure node
                fail_node_id = f"{step_id}_fail"
                self._add_node(
                    node_id=fail_node_id,
                    node_type="result",
                    label="❌ Failed",
                    status="failed",
                    data={
                        "tool": step.tool_name,
                        "error": str(e),
                    },
                    position={"x": 500, "y": i * 100}
                )
                self._add_edge(step_id, fail_node_id, style={"stroke": "#ef4444", "strokeWidth": 2})
                
                # Log audit entry
                await self._log_audit(
                    action_type=ActionType.READ,  # Default to READ for failed attempts
                    tool_name=step.tool_name,
                    description=step.description,
                    input_data=step.parameters,
                    error_message=str(e),
                    status=ExecutionStatus.FAILED,
                )
                
                # Stop execution on failure
                trace.status = ExecutionStatus.FAILED
                trace.completed_at = datetime.utcnow()
                break
        
        # Finalize trace
        if not has_pending_approval and trace.status != ExecutionStatus.FAILED:
            trace.status = ExecutionStatus.SUCCESS
            trace.completed_at = datetime.utcnow()
        
        trace.nodes = [node.model_dump() for node in self.nodes]
        trace.edges = [edge.model_dump() for edge in self.edges]
        trace.final_result = final_result
        
        await self.db.commit()
        await self.db.refresh(trace)
        
        return {
            "task_id": self.task_id,
            "success": trace.status == ExecutionStatus.SUCCESS,
            "status": trace.status.value,
            "result": final_result,
            "execution_trace": {
                "nodes": [node.model_dump() for node in self.nodes],
                "edges": [edge.model_dump() for edge in self.edges],
            },
            "requires_approval": has_pending_approval,
            "pending_actions": self.pending_approvals,
            "message": "Task completed successfully" if trace.status == ExecutionStatus.SUCCESS 
                      else "Task requires approval" if has_pending_approval
                      else "Task failed",
        }
    
    def _add_node(
        self,
        node_id: str,
        node_type: str,
        label: str,
        status: str,
        data: Dict[str, Any],
        position: Optional[Dict[str, float]] = None
    ):
        """Add a node to the flow graph."""
        if position is None:
            position = {"x": 0, "y": 0}
        
        node = FlowNode(
            id=node_id,
            type=node_type,
            label=label,
            status=status,
            data=data,
            position=position,
        )
        self.nodes.append(node)
    
    def _add_edge(
        self,
        source: str,
        target: str,
        label: Optional[str] = None,
        animated: bool = False,
        style: Optional[Dict[str, Any]] = None
    ):
        """Add an edge to the flow graph."""
        edge = FlowEdge(
            id=f"{source}_{target}",
            source=source,
            target=target,
            label=label,
            animated=animated,
            style=style,
        )
        self.edges.append(edge)
    
    async def _log_audit(
        self,
        action_type: ActionType,
        tool_name: str,
        description: str,
        input_data: Dict[str, Any],
        status: ExecutionStatus,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        requires_approval: bool = False,
    ):
        """Log an audit entry for the action."""
        audit_log = AuditLog(
            task_id=self.task_id,
            action_type=action_type,
            tool_name=tool_name,
            action_description=description,
            input_data=input_data,
            output_data=output_data,
            status=status,
            error_message=error_message,
            requires_approval=requires_approval,
        )
        self.db.add(audit_log)


# Factory function
def create_flow_engine(db: AsyncSession, task_id: Optional[str] = None) -> FlowEngine:
    """Create a new FlowEngine instance."""
    if task_id is None:
        task_id = str(uuid.uuid4())
    return FlowEngine(db, task_id)
