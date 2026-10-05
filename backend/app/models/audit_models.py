"""
Audit models for tracking agent actions and execution traces.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.session import Base


class ActionType(enum.Enum):
    """Types of actions that can be performed."""
    READ = "read"
    LOW_RISK_WRITE = "low_risk_write"
    HIGH_RISK_WRITE = "high_risk_write"


class ExecutionStatus(enum.Enum):
    """Status of an execution step."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class AuditLog(Base):
    """Audit log for tracking all agent actions."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), nullable=False, index=True)  # Unique task identifier
    action_type = Column(SQLEnum(ActionType), nullable=False)
    tool_name = Column(String(100), nullable=False)
    action_description = Column(Text)
    input_data = Column(JSON)
    output_data = Column(JSON)
    status = Column(SQLEnum(ExecutionStatus), default=ExecutionStatus.PENDING)
    error_message = Column(Text)
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(String(255))  # User ID or 'system' for auto-approved
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, task_id='{self.task_id}', tool='{self.tool_name}')>"


class ExecutionTrace(Base):
    """Complete execution trace for a task."""
    __tablename__ = "execution_traces"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, nullable=False, index=True)
    user_request = Column(Text, nullable=False)
    agent_plan = Column(JSON)  # The plan returned by Agent Core
    nodes = Column(JSON)  # React Flow nodes
    edges = Column(JSON)  # React Flow edges
    final_result = Column(JSON)
    status = Column(SQLEnum(ExecutionStatus), default=ExecutionStatus.PENDING)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<ExecutionTrace(task_id='{self.task_id}', status='{self.status.value}')>"
