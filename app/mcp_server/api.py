"""Public MCP interface"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from app.mcp_server.models import OrderItemRequest, OrderRequest

from app.mcp_server.legacy_client import fetch_menu, fetch_inventory
from app.mcp_server.validator import (
    validate_item_exists, 
    validate_quantity, 
    check_inventory,
    match_menu_item,
)

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

@app.post("/mcp/validate-order-items")
def validate_order_items(items: List[OrderItemRequest]):
    """
    Single endpoint that:
    1. Matches user terms to menu items
    2. Checks inventory for each
    3. Returns complete validation result
    """
    results = []
    all_available = True
    legacy_menu = fetch_menu()
    inventory = fetch_inventory()
    
    for item in items:
        item_name = item.name
        quantity = item.quantity
        
        # 1) Match to menu item
        matched_item = match_menu_item(item_name, legacy_menu["menu_items"])
        if not matched_item:
            results.append({
                "requested_name": item_name,
                "found": False,
                "available": False,
                "reason": "Item not found in menu"
            })
            all_available = False
            continue
        
        # 2) Check inventory
        available, reason = check_inventory(matched_item["item_code"], inventory)
        results.append({
            "requested_name": item_name,
            "found": True,
            "item_code": matched_item["item_code"],
            "menu_name": matched_item["name"],
            "price": matched_item["price_inr"],
            "quantity": quantity,
            "available": available,
            "reason": reason
        })
        if not available:
            all_available = False
            
    return {
        "all_available": all_available,
        "results": results
    }    
   
    
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