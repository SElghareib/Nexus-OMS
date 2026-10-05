"""
Pydantic schemas for OMS models.
Used for request/response validation.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class OrderStatusEnum(str, Enum):
    """Order status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    STUCK = "stuck"
    REFUNDED = "refunded"


# Customer Schemas
class CustomerBase(BaseModel):
    email: str = Field(..., example="customer@example.com")
    name: str = Field(..., example="John Doe")
    tier: str = Field(default="standard", example="premium")


class CustomerCreate(CustomerBase):
    pass


class CustomerResponse(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# Product Schemas
class ProductBase(BaseModel):
    sku: str = Field(..., example="PROD-001")
    name: str = Field(..., example="Widget Pro")
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    stock_level: int = Field(default=0, ge=0)


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# Order Schemas
class OrderItem(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)


class OrderBase(BaseModel):
    customer_id: int
    total_amount: float = Field(default=0.0, ge=0)
    discount_percent: float = Field(default=0.0, ge=0, le=100)
    items: List[OrderItem] = Field(default_factory=list)
    shipping_address: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    status: Optional[OrderStatusEnum] = None
    discount_percent: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = None
    is_stuck: Optional[bool] = None
    stuck_reason: Optional[str] = None


class OrderResponse(OrderBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    status: OrderStatusEnum
    is_stuck: bool
    stuck_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
