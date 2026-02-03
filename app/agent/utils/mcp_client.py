"""
MCP Client - HTTP client for MCP server communication.
1. check_inventory - Check item availability
2. submit_order - Submit validated order
3. validate_order_items - Validate and match items
4. MCPClient class - Full client with menu access
"""

import requests
from app.config import settings


MCP_BASE_URL = settings.mcp_base_url
MCP_TIMEOUT = settings.mcp_timeout

class MCPClient:
    """
    Full MCP server client.
    1. get_menu() - Fetches full menu
    2. get_inventory() - Fetches inventory status
    """
    
    def __init__(self, base_url: str = MCP_BASE_URL):
        """
        Initializes MCP client.
        
        Args:
            base_url: MCP server URL (default localhost:8001)
        """
        self.base_url = base_url
    
    def get_menu(self) -> list:
        """
        Fetches full menu from legacy system.
        1. Calls /mcp/menu endpoint
        2. Returns list of menu items
        
        Returns:
            list: menu items with name, price, category
        """
        r = requests.get(f"{self.base_url}/mcp/menu")
        r.raise_for_status()
        return r.json()
    
    def get_inventory(self) -> dict:
        """
        Fetches inventory status from legacy system.
        1. Calls /mcp/inventory endpoint
        2. Returns stock levels and machine status
        
        Returns:
            dict: inventory data
        """
        r = requests.get(f"{self.base_url}/mcp/inventory")
        r.raise_for_status()
        return r.json()

# TODO: Add timeout handling and retries as needed
# TODO: Add logging for requests and responses
# TODO: Add these fucntions to above class
def check_inventory(item_name: str) -> dict:
    """
    Checks inventory for specific item.
    1. Calls /mcp/inventory/{item_name}
    2. Returns availability and reason
    
    Args:
        item_name: item to check 
    Returns:
        dict: {available: bool, reason: str}
    """
    r = requests.get(f"{MCP_BASE_URL}/mcp/inventory/{item_name}")
    r.raise_for_status()
    return r.json()


def submit_order(order: dict) -> dict:
    """
    Submits validated order to legacy system.
    
    1. Posts order to /mcp/order
    2. Returns confirmation
    
    Args:
        order: {item_code: str, quantity: int}
    
    Returns:
        dict: Order confirmation
    """
    r = requests.post(f"{MCP_BASE_URL}/mcp/order", json=order)
    r.raise_for_status()
    return r.json()


def validate_order_items(items: list) -> dict:
    """
    Validates items against menu and inventory.
    
    1. Posts items to /mcp/validate-order-items
    2. Returns validation results with matched items
    
    Note: Uses fuzzy matching for voice transcription errors.
    
    Args:
        items: [{name: str, quantity: int}, ...]
    
    Returns:
        dict: {results: [{found, available, menu_name, reason}, ...]}
    """
    r = requests.post(f"{MCP_BASE_URL}/mcp/validate-order-items", json=items)
    r.raise_for_status()
    return r.json()
