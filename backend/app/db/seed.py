"""
Database seeding script for Nexus OMS.
Populates the database with realistic dummy data including stuck orders.
"""
import asyncio
import random
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.db.session import Base
from app.models.oms_models import Customer, Product, Order, OrderStatus


# Configuration
NUM_CUSTOMERS = 50
NUM_PRODUCTS = 100
NUM_ORDERS = 200
STUCK_ORDER_PERCENTAGE = 0.15  # 15% of orders will be stuck


async def seed_database():
    """Seed the database with dummy data."""
    print("Starting database seeding...")
    
    # Create engine and session
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session_maker() as db:
        # Check if already seeded
        result = await db.execute(select(Customer))
        existing_customers = result.scalars().first()
        
        if existing_customers:
            print("Database already seeded. Skipping.")
            return
        
        # Seed Customers
        print(f"Creating {NUM_CUSTOMERS} customers...")
        customers = []
        tiers = ["standard", "premium", "vip"]
        
        for i in range(NUM_CUSTOMERS):
            customer = Customer(
                email=f"customer{i+1}@example.com",
                name=f"Customer {i+1}",
                tier=random.choice(tiers),
            )
            customers.append(customer)
            db.add(customer)
        
        await db.commit()
        print(f"✓ Created {len(customers)} customers")
        
        # Seed Products
        print(f"Creating {NUM_PRODUCTS} products...")
        products = []
        product_names = [
            "Widget", "Gadget", "Device", "Tool", "Instrument",
            "Apparatus", "Machine", "Component", "Module", "Unit"
        ]
        product_adjectives = [
            "Pro", "Plus", "Max", "Ultra", "Elite", "Basic", "Standard", 
            "Advanced", "Premium", "Deluxe", "Mini", "Mega"
        ]
        
        for i in range(NUM_PRODUCTS):
            sku = f"PROD-{i+1:04d}"
            name = f"{random.choice(product_adjectives)} {random.choice(product_names)} {i+1}"
            product = Product(
                sku=sku,
                name=name,
                description=f"High-quality {name.lower()} for all your needs",
                price=round(random.uniform(9.99, 999.99), 2),
                stock_level=random.randint(0, 500),
            )
            products.append(product)
            db.add(product)
        
        await db.commit()
        print(f"✓ Created {len(products)} products")
        
        # Seed Orders
        print(f"Creating {NUM_ORDERS} orders...")
        orders = []
        statuses = list(OrderStatus)
        
        for i in range(NUM_ORDERS):
            customer = random.choice(customers)
            
            # Generate order items
            num_items = random.randint(1, 5)
            order_items = []
            base_total = 0
            
            for _ in range(num_items):
                product = random.choice(products)
                quantity = random.randint(1, 10)
                item_total = product.price * quantity
                base_total += item_total
                
                order_items.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "quantity": quantity,
                    "price": product.price,
                })
            
            # Calculate final total with random discount
            discount = random.choice([0, 5, 10, 15, 20])
            final_total = base_total * (1 - discount / 100)
            
            # Determine if this order should be stuck
            is_stuck = random.random() < STUCK_ORDER_PERCENTAGE
            
            # Choose status - stuck orders are more likely to have problematic statuses
            if is_stuck:
                status = random.choice([
                    OrderStatus.PENDING, 
                    OrderStatus.PROCESSING,
                    OrderStatus.STUCK
                ])
                stuck_reasons = [
                    "Payment verification required",
                    "Inventory shortage detected",
                    "Shipping address incomplete",
                    "Customer requested hold",
                    "Fraud detection review",
                ]
                stuck_reason = random.choice(stuck_reasons)
            else:
                status = random.choice(statuses)
                stuck_reason = None
            
            # Random order date within last 30 days
            days_ago = random.randint(0, 30)
            created_at = datetime.utcnow() - timedelta(days=days_ago)
            
            order = Order(
                customer_id=customer.id,
                status=status,
                total_amount=round(final_total, 2),
                discount_percent=discount,
                items=order_items,
                shipping_address={
                    "street": f"{random.randint(100, 9999)} Main St",
                    "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                    "state": random.choice(["NY", "CA", "IL", "TX", "AZ"]),
                    "zip": f"{random.randint(10000, 99999)}",
                },
                notes=f"Order #{i+1} - Generated by seed script",
                is_stuck=is_stuck,
                stuck_reason=stuck_reason,
            )
            # Override created_at (SQLAlchemy usually handles this automatically)
            order.created_at = created_at
            
            orders.append(order)
            db.add(order)
        
        await db.commit()
        print(f"✓ Created {len(orders)} orders")
        
        # Summary
        stuck_count = sum(1 for o in orders if o.is_stuck)
        print(f"\n{'='*50}")
        print("Seeding complete!")
        print(f"{'='*50}")
        print(f"Customers: {len(customers)}")
        print(f"Products: {len(products)}")
        print(f"Orders: {len(orders)}")
        print(f"Stuck Orders: {stuck_count} ({stuck_count/len(orders)*100:.1f}%)")
        print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(seed_database())
