"""
HTTP client for communicating with Agent Core (Project 1).
Sends tasks and receives execution plans.
"""
import httpx
from typing import Optional, Dict, Any
import logging

from app.core.config import settings
from app.schemas.agent_schemas import AgentTaskRequest, AgentPlanResponse

logger = logging.getLogger(__name__)


class AgentClientError(Exception):
    """Exception raised when Agent Core communication fails."""
    pass


class AgentClient:
    """Client for interacting with the external Agent Core service."""
    
    def __init__(self):
        self.base_url = settings.AGENT_CORE_URL
        self.timeout = 30.0  # seconds
    
    async def send_task(self, request: AgentTaskRequest) -> AgentPlanResponse:
        """
        Send a task to Agent Core and receive an execution plan.
        
        Args:
            request: The task request with natural language description
            
        Returns:
            AgentPlanResponse with the execution plan
            
        Raises:
            AgentClientError: If communication fails
        """
        url = f"{self.base_url}/api/v1/agent/plan"
        
        payload = {
            "task": request.task_description,
            "context": {
                "order_id": request.order_id,
                "customer_id": request.customer_id,
            } if request.order_id or request.customer_id else {}
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # Parse response into AgentPlanResponse
                return AgentPlanResponse(
                    success=data.get("success", True),
                    plan=[
                        {
                            "step_number": step.get("step", i),
                            "tool_name": step.get("tool", ""),
                            "description": step.get("description", ""),
                            "parameters": step.get("parameters", {}),
                            "permission_level": step.get("permission_level", "read")
                        }
                        for i, step in enumerate(data.get("plan", []))
                    ],
                    reasoning=data.get("reasoning", ""),
                    estimated_steps=len(data.get("plan", []))
                )
                
        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to Agent Core at {self.base_url}")
            raise AgentClientError("Agent Core timed out. Please try again.")
        except httpx.ConnectionError:
            logger.error(f"Cannot connect to Agent Core at {self.base_url}")
            raise AgentClientError(
                f"Cannot connect to Agent Core. Ensure it's running at {self.base_url}"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Agent Core returned error: {e.response.status_code}")
            raise AgentClientError(f"Agent Core error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error communicating with Agent Core: {e}")
            raise AgentClientError(f"Failed to get plan from Agent Core: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if Agent Core is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False


# Singleton instance
agent_client = AgentClient()
