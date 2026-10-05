"""
API routes for OMS resources (Orders, Customers, Products).
Standard CRUD endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.models.oms_models import Order, Customer, Product, OrderStatus
from app.schemas.oms_schemas import (
    OrderResponse, OrderCreate, OrderUpdate,
    CustomerResponse, CustomerCreate,
    ProductResponse, ProductCreate,
)

router = APIRouter(prefix="/api/v1", tags=["orders"])


@router.get("/orders", response_model=List[OrderResponse])
async def list_orders(
    skip: int = 0,
    limit: int = 50,
    status_filter: str = None,
    db: AsyncSession = Depends(get_db)
):
    """List all orders with optional status filter."""
    query = select(Order)
    
    if status_filter:
        try:
            order_status = OrderStatus(status_filter)
            query = query.where(Order.status == order_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}"
            )
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    orders = result.scalars().all()
    
    return orders


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific order by ID."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order_data: OrderCreate, db: AsyncSession = Depends(get_db)):
    """Create a new order."""
    # Verify customer exists
    result = await db.execute(select(Customer).where(Customer.id == order_data.customer_id))
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Calculate total from items
    total = sum(item.price * item.quantity for item in order_data.items)
    total = total * (1 - order_data.discount_percent / 100)
    
    order = Order(
        customer_id=order_data.customer_id,
        total_amount=total,
        discount_percent=order_data.discount_percent,
        items=[item.model_dump() for item in order_data.items],
        shipping_address=order_data.shipping_address,
        notes=order_data.notes,
    )
    
    db.add(order)
    await db.commit()
    await db.refresh(order)
    
    return order


@router.patch("/orders/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing order."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Update fields
    if order_data.status is not None:
        order.status = OrderStatus(order_data.status.value)
    if order_data.discount_percent is not None:
        order.discount_percent = order_data.discount_percent
    if order_data.notes is not None:
        order.notes = order_data.notes
    if order_data.is_stuck is not None:
        order.is_stuck = order_data.is_stuck
    if order_data.stuck_reason is not None:
        order.stuck_reason = order_data.stuck_reason
    
    await db.commit()
    await db.refresh(order)
    
    return order


@router.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(order_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an order."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    await db.delete(order)
    await db.commit()
