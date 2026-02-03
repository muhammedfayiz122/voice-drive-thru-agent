"""
MCP Server API - Public interface for agent communication.

1. /mcp/menu - Returns full menu
2. /mcp/validate-order-items - Validates items with fuzzy matching
3. /mcp/inventory/{item_code} - Checks specific item availability
4. /mcp/order - Submits validated order

Note: All endpoints validate against legacy system data.
"""

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
    """
    Returns full menu in normalized format.
    
    1. Fetches menu from legacy system
    2. Normalizes to MCP format (id, name, price)
    
    Returns:
        dict: {menu: [{id, name, price}, ...]}
    """
    legacy_menu = fetch_menu()
    
    # Normalize Legacy Menu to MCP Menu format
    mcp_menu = [
        {
            "id": item["item_code"],
            "name": item["name"],
            "price": item["price_inr"],
            "category": item.get("category", "Other")
        }
        for item in legacy_menu["menu_items"]
    ]
    
    return mcp_menu


@app.post("/mcp/validate-order-items")
def validate_order_items(items: List[OrderItemRequest]):
    """
    Validates items against menu and inventory.
    
    1. Fuzzy matches user input to menu items
    2. Checks inventory for each matched item
    3. Returns complete validation results
    
    Args:
        items: List of {name: str, quantity: int}
    
    Returns:
        dict: {all_available: bool, results: [{found, available, ...}, ...]}
    """
    results = []
    all_available = True
    legacy_menu = fetch_menu()
    inventory = fetch_inventory()
    
    for item in items:
        item_name = item.name
        quantity = item.quantity
        
        # 1) Match to menu item (uses fuzzy matching)
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
   
@app.get("/mcp/inventory")
def get_full_inventory():
    """Returns full inventory status."""
    return fetch_inventory()
    
@app.get("/mcp/inventory/{item_code}")
def get_item_availability(item_code: str):
    """
    Checks availability of specific item by code.
    
    1. Validates item exists in menu
    2. Checks inventory and machine status
    3. Returns deterministic availability decision
    
    Note: Agent should not interpret raw inventory data.
    
    Args:
        item_code: System item code (e.g., "PZ001")
    
    Returns:
        dict: {item_code, available, reason}
    
    Raises:
        HTTPException 404: If item not found
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
    Final order submission with validation.
    
    1. Validates item exists
    2. Validates quantity (0-10)
    3. Validates availability
    4. Accepts order if all pass
    
    Note: Last safety gate before KDS/order execution.
    
    Args:
        order: {item_code: str, quantity: int}
    
    Returns:
        dict: {status, item_code, quantity}
    """
    menu = fetch_menu()
    inventory = fetch_inventory()
    
    # Validate user item exists on legacy_menu 
    if not validate_item_exists(order.item_code, menu["menu_items"]):
        raise HTTPException(status_code=404, detail="Invalid menu item")
    
    # Validate quantity is within acceptable range
    # NOTE: This is a business rule, e.g., max 10 per item
    if not validate_quantity(order.quantity):
        raise HTTPException(status_code=400, detail="Invalid quantity")
    
    # Validate item is available in inventory
    available, reason = check_inventory(order.item_code, inventory)
    if not available:
        raise HTTPException(status_code=400, detail=f"Item not available: {reason}")
    
    return {
        "status": "Order accepted",
        "item_code": order.item_code,
        "quantity": order.quantity
    }