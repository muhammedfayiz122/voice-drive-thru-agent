"""Public MCP interface"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.mcp_server.legacy_client import fetch_menu, fetch_inventory
from app.mcp_server.validator import validate_item_exists, validate_quantity, check_inventory

app = FastAPI()

@app.get("/mcp/menu")
def get_menu():
    """Get menu endpoint"""
    legacy_menu = fetch_menu()
    
    # NOrmalize Legacy Menu to MCP Menu format
    mcp_menu = [
        {
            "id": item["item_code"],
            "name": item["name"],
            "price": item["price_inr"]
        }
        for item in legacy_menu["menu_items"]
    ]
    
    return {"menu": mcp_menu}


@app.get("/mcp/inventory/{item_code}")
def get_item_availability(item_code: str):
    """
    Checks availability of a specific item in a safe, deterministic way.

    Purpose:
    1) Validates that the requested item actually exists in the menu
    2) Evaluates inventory state and machine dependencies
    
    Returns a decision (available / not available) with reasoning

    Why this exists:
    - The AI agent should not interpret raw inventory data
    - Availability decisions must be deterministic and rule-based
    - Prevents hallucinated or unsafe ordering actions
    """
    menu = fetch_menu()
    inventory = fetch_inventory()
    
    if not validate_item_exists(item_code, menu["menu_items"]):
        raise HTTPException(status_code=404, detail="Invalid menu item")
    
    available, reason = check_inventory(item_code, inventory)
    return {
        "item_code": item_code,
        "available": available, 
        "reason": reason
    }

class OrderRequest(BaseModel):
    item_code: str
    quantity: int

@app.post("/mcp/order")
def submit_order(order: OrderRequest):
    """
    Accepts and validates a final order request before submission.

    Purpose:
    - Performs final validation before an order is sent downstream
    - Ensures item existence, valid quantity, and availability
    - Acts as the last safety gate before KDS / order execution

    Why this exists:
    - AI agents are probabilistic and must not place unchecked orders
    - Legacy systems should not receive invalid or hallucinated requests
    - MCP enforces strict business rules before order submission
    """
    menu = fetch_menu()
    inventory = fetch_inventory()
    
    if not validate_item_exists(order.item_code, menu["menu_items"]):
        raise HTTPException(status_code=404, detail="Invalid menu item")
    
    if not validate_quantity(order.quantity):
        raise HTTPException(status_code=400, detail="Invalid quantity")
    
    available, reason = check_inventory(order.item_code, inventory)
    if not available:
        raise HTTPException(status_code=400, detail=f"Item not available: {reason}")
    
    return {
        "status": "Order accepted",
        "item_code": order.item_code,
        "quantity": order.quantity
    }