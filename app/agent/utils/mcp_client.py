import requests

MCP_BASE_URL = "http://localhost:8001"

def check_inventory(item_name: str) -> dict:
    r = requests.get(f"{MCP_BASE_URL}/mcp/inventory/{item_name}")
    r.raise_for_status()
    return r.json()

def submit_order(order: dict) -> dict:
    r = requests.post(f"{MCP_BASE_URL}/mcp/order", json=order)
    r.raise_for_status()
    return r.json()

def search_menu(item_name: str) -> dict:
    r = requests.get(f"{MCP_BASE_URL}/mcp/menu/{item_name}")
    r.raise_for_status()
    return r.json()
