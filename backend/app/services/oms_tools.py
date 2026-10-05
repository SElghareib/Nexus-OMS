"""
OMS Tools - Business logic functions that the Agent can call.
These tools execute real SQL queries and enforce permissions.
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.models.oms_models import Order, Customer, Product, OrderStatus
from app.schemas.oms_schemas import OrderUpdate
from app.models.audit_models import ActionType

logger = logging.getLogger(__name__)


class ToolError(Exception):
    """Exception raised when a tool execution fails."""
    pass


class PermissionDenied(Exception):
    """Exception raised when an action requires higher permission level."""
    pass


# ============================================================================
# READ OPERATIONS (No approval needed)
# ============================================================================

async def get_order_details(db: AsyncSession, order_id: int) -> Dict[str, Any]:
    """
    Retrieve complete order details by ID.
    Permission: READ
    """
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise ToolError(f"Order {order_id} not found")
    
    return {
        "id": order.id,
        "customer_id": order.customer_id,
        "status": order.status.value,
        "total_amount": order.total_amount,
        "discount_percent": order.discount_percent,
        "items": order.items,
        "shipping_address": order.shipping_address,
        "notes": order.notes,
        "is_stuck": order.is_stuck,
        "stuck_reason": order.stuck_reason,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }


async def get_customer_details(db: AsyncSession, customer_id: int) -> Dict[str, Any]:
    """
    Retrieve customer details by ID.
    Permission: READ
    """
    result = await db.execute(
        select(Customer)
        .where(Customer.id == customer_id)
    )
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise ToolError(f"Customer {customer_id} not found")
    
    return {
        "id": customer.id,
        "email": customer.email,
        "name": customer.name,
        "tier": customer.tier,
        "created_at": customer.created_at.isoformat() if customer.created_at else None,
    }


async def check_inventory(db: AsyncSession, sku: str) -> Dict[str, Any]:
    """
    Check current stock level for a product SKU.
    Permission: READ
    """
    result = await db.execute(
        select(Product)
        .where(Product.sku == sku)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise ToolError(f"Product with SKU {sku} not found")
    
    return {
        "product_id": product.id,
        "sku": product.sku,
        "name": product.name,
        "stock_level": product.stock_level,
        "price": product.price,
    }


async def search_orders_by_status(
    db: AsyncSession, 
    status: str, 
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Search for orders by status.
    Permission: READ
    """
    try:
        order_status = OrderStatus(status)
    except ValueError:
        raise ToolError(f"Invalid order status: {status}")
    
    result = await db.execute(
        select(Order)
        .where(Order.status == order_status)
        .limit(limit)
    )
    orders = result.scalars().all()
    
    return [
        {
            "id": order.id,
            "customer_id": order.customer_id,
            "status": order.status.value,
            "total_amount": order.total_amount,
            "is_stuck": order.is_stuck,
        }
        for order in orders
    ]


# ============================================================================
# LOW-RISK WRITE OPERATIONS (Auto-approved)
# ============================================================================

async def update_order_status(
    db: AsyncSession, 
    order_id: int, 
    new_status: str
) -> Dict[str, Any]:
    """
    Update the status of an order.
    Permission: LOW_RISK_WRITE
    """
    try:
        order_status = OrderStatus(new_status)
    except ValueError:
        raise ToolError(f"Invalid order status: {new_status}")
    
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise ToolError(f"Order {order_id} not found")
    
    old_status = order.status.value
    order.status = order_status
    
    # If moving out of stuck state, clear the flag
    if order.is_stuck and new_status != "stuck":
        order.is_stuck = False
        order.stuck_reason = None
    
    return {
        "order_id": order_id,
        "old_status": old_status,
        "new_status": new_status,
        "success": True,
    }


async def apply_discount(
    db: AsyncSession, 
    order_id: int, 
    discount_percent: float
) -> Dict[str, Any]:
    """
    Apply a discount percentage to an order.
    Permission: LOW_RISK_WRITE
    """
    if discount_percent < 0 or discount_percent > 100:
        raise ToolError("Discount must be between 0 and 100")
    
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise ToolError(f"Order {order_id} not found")
    
    old_discount = order.discount_percent
    order.discount_percent = discount_percent
    
    # Recalculate total
    base_total = sum(item.get("price", 0) * item.get("quantity", 0) for item in order.items)
    order.total_amount = base_total * (1 - discount_percent / 100)
    
    return {
        "order_id": order_id,
        "old_discount": old_discount,
        "new_discount": discount_percent,
        "new_total": order.total_amount,
        "success": True,
    }


async def add_order_notes(
    db: AsyncSession, 
    order_id: int, 
    notes: str
) -> Dict[str, Any]:
    """
    Add or update notes on an order.
    Permission: LOW_RISK_WRITE
    """
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise ToolError(f"Order {order_id} not found")
    
    old_notes = order.notes
    order.notes = notes
    
    return {
        "order_id": order_id,
        "old_notes": old_notes,
        "new_notes": notes,
        "success": True,
    }


# ============================================================================
# HIGH-RISK WRITE OPERATIONS (Require approval)
# ============================================================================

async def cancel_order(
    db: AsyncSession, 
    order_id: int,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cancel an order.
    Permission: HIGH_RISK_WRITE - Requires approval
    """
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise ToolError(f"Order {order_id} not found")
    
    if order.status == OrderStatus.SHIPPED:
        raise ToolError("Cannot cancel an order that has already been shipped")
    
    old_status = order.status.value
    order.status = OrderStatus.CANCELLED
    order.is_stuck = False
    order.stuck_reason = reason
    
    return {
        "order_id": order_id,
        "old_status": old_status,
        "new_status": "cancelled",
        "reason": reason,
        "success": True,
        "requires_approval": True,
    }


async def issue_refund(
    db: AsyncSession, 
    order_id: int,
    amount: Optional[float] = None
) -> Dict[str, Any]:
    """
    Issue a refund for an order.
    Permission: HIGH_RISK_WRITE - Requires approval
    """
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise ToolError(f"Order {order_id} not found")
    
    if order.status not in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
        raise ToolError("Can only refund delivered or cancelled orders")
    
    refund_amount = amount if amount is not None else order.total_amount
    
    order.status = OrderStatus.REFUNDED
    
    return {
        "order_id": order_id,
        "refund_amount": refund_amount,
        "success": True,
        "requires_approval": True,
    }


async def mark_order_stuck(
    db: AsyncSession, 
    order_id: int,
    reason: str
) -> Dict[str, Any]:
    """
    Mark an order as stuck requiring intervention.
    Permission: HIGH_RISK_WRITE - Requires approval
    """
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise ToolError(f"Order {order_id} not found")
    
    order.is_stuck = True
    order.stuck_reason = reason
    
    return {
        "order_id": order_id,
        "is_stuck": True,
        "reason": reason,
        "success": True,
        "requires_approval": True,
    }


# ============================================================================
# Tool Registry
# ============================================================================

TOOL_REGISTRY = {
    "get_order": {
        "function": get_order_details,
        "description": "Retrieve order details by order ID",
        "permission_level": ActionType.READ,
        "requires_approval": False,
        "parameters": {
            "order_id": {"type": "integer", "description": "The order ID"}
        },
    },
    "get_customer": {
        "function": get_customer_details,
        "description": "Retrieve customer details by customer ID",
        "permission_level": ActionType.READ,
        "requires_approval": False,
        "parameters": {
            "customer_id": {"type": "integer", "description": "The customer ID"}
        },
    },
    "check_inventory": {
        "function": check_inventory,
        "description": "Check stock level for a product SKU",
        "permission_level": ActionType.READ,
        "requires_approval": False,
        "parameters": {
            "sku": {"type": "string", "description": "Product SKU"}
        },
    },
    "search_orders": {
        "function": search_orders_by_status,
        "description": "Search for orders by status",
        "permission_level": ActionType.READ,
        "requires_approval": False,
        "parameters": {
            "status": {"type": "string", "description": "Order status to filter by"},
            "limit": {"type": "integer", "description": "Maximum results to return"}
        },
    },
    "update_order_status": {
        "function": update_order_status,
        "description": "Update the status of an order",
        "permission_level": ActionType.LOW_RISK_WRITE,
        "requires_approval": False,
        "parameters": {
            "order_id": {"type": "integer", "description": "The order ID"},
            "new_status": {"type": "string", "description": "New status value"}
        },
    },
    "apply_discount": {
        "function": apply_discount,
        "description": "Apply a discount percentage to an order",
        "permission_level": ActionType.LOW_RISK_WRITE,
        "requires_approval": False,
        "parameters": {
            "order_id": {"type": "integer", "description": "The order ID"},
            "discount_percent": {"type": "number", "description": "Discount percentage (0-100)"}
        },
    },
    "add_order_notes": {
        "function": add_order_notes,
        "description": "Add or update notes on an order",
        "permission_level": ActionType.LOW_RISK_WRITE,
        "requires_approval": False,
        "parameters": {
            "order_id": {"type": "integer", "description": "The order ID"},
            "notes": {"type": "string", "description": "Notes text"}
        },
    },
    "cancel_order": {
        "function": cancel_order,
        "description": "Cancel an order (requires approval)",
        "permission_level": ActionType.HIGH_RISK_WRITE,
        "requires_approval": True,
        "parameters": {
            "order_id": {"type": "integer", "description": "The order ID"},
            "reason": {"type": "string", "description": "Cancellation reason"}
        },
    },
    "issue_refund": {
        "function": issue_refund,
        "description": "Issue a refund for an order (requires approval)",
        "permission_level": ActionType.HIGH_RISK_WRITE,
        "requires_approval": True,
        "parameters": {
            "order_id": {"type": "integer", "description": "The order ID"},
            "amount": {"type": "number", "description": "Refund amount (optional, defaults to full order total)"}
        },
    },
    "mark_order_stuck": {
        "function": mark_order_stuck,
        "description": "Mark an order as stuck requiring intervention (requires approval)",
        "permission_level": ActionType.HIGH_RISK_WRITE,
        "requires_approval": True,
        "parameters": {
            "order_id": {"type": "integer", "description": "The order ID"},
            "reason": {"type": "string", "description": "Reason why order is stuck"}
        },
    },
}


def get_tool_info(tool_name: str) -> Optional[Dict[str, Any]]:
    """Get information about a tool by name."""
    return TOOL_REGISTRY.get(tool_name)


def list_available_tools() -> List[Dict[str, Any]]:
    """List all available tools with their metadata."""
    return [
        {
            "name": name,
            "description": info["description"],
            "permission_level": info["permission_level"].value,
            "requires_approval": info["requires_approval"],
            "parameters": info["parameters"],
        }
        for name, info in TOOL_REGISTRY.items()
    ]
