"""
KDS API - FastAPI endpoints for receiving orders.

1. POST /kds/order - Submit order to KDS display
2. GET /kds/orders - Get all current orders
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import threading

from app.kds.order_store import get_order_store
from app.kds.models import OrderStatus


class KDSOrderItem(BaseModel):
    """Item in KDS order."""
    item_code: str
    name: str
    quantity: int
    price: float = 0.0


class KDSOrderRequest(BaseModel):
    """Order submission request."""
    items: List[KDSOrderItem]


app = FastAPI(title="KDS API", description="Kitchen Display System API")


@app.post("/kds/order")
def submit_to_kds(order: KDSOrderRequest):
    """
    Submit order to KDS display.
    
    Args:
        order: Order with list of items
        
    Returns:
        dict: {order_id, status, item_count}
    """
    if not order.items:
        raise HTTPException(status_code=400, detail="Order must have at least one item")
    
    store = get_order_store()
    items_data = [item.model_dump() for item in order.items]
    order_id = store.add_order(items_data)
    
    return {
        "order_id": order_id,
        "status": "received",
        "item_count": len(order.items)
    }


@app.get("/kds/orders")
def get_orders(status: Optional[str] = None):
    """
    Get all orders, optionally filtered by status.
    
    Args:
        status: Filter by status (pending, in_progress, completed)
        
    Returns:
        list: Orders with items
    """
    store = get_order_store()
    orders = store.get_all_orders()
    
    if status:
        try:
            filter_status = OrderStatus(status)
            orders = [o for o in orders if o.status == filter_status]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    return [
        {
            "order_id": o.order_id,
            "status": o.status.value,
            "items": [
                {
                    "item_code": item.item_code,
                    "name": item.name,
                    "quantity": item.quantity,
                    "price": item.price
                }
                for item in o.items
            ],
            "total": o.total,
            "created_at": o.created_at.isoformat()
        }
        for o in orders
    ]


@app.get("/kds/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "kds"}
