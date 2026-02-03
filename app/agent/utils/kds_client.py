"""
KDS client - HTTP client for KDS (Kitchen Display System) communication.
1. submit_order - Submit order to KDS display
2. get_orders - Get all current orders
3. health_check - Check KDS service status
4. KDSClient class - Full client with all operations
"""

import requests
from typing import Optional

KDS_BASE_URL = "http://127.0.0.1:8002"

class KDSClient:
    """
    Full KDS server client.
    
    1. submit_order() - Sends order to KDS display
    2. get_orders() - Fetches all orders
    3. health_check() - Checks KDS status
    
    Note: Used for order display and kitchen management.
    """
    
    def __init__(self, base_url: str = KDS_BASE_URL):
        """
        Initializes KDS client.
        
        Args:
            base_url: KDS server URL (default localhost:8001)
        """
        self.base_url = base_url
    
    def submit_order(self, items: list) -> dict:
        """
        Submits order to KDS display.
        
        1. Calls POST /kds/order endpoint
        2. Returns order confirmation with order_id
        
        Args:
            items: List of items [{item_code, name, quantity, price}, ...]
        
        Returns:
            dict: {order_id, status, item_count}
        """
        r = requests.post(
            f"{self.base_url}/kds/order",
            json={"items": items},
            timeout=5.0
        )
        r.raise_for_status()
        return r.json()
    
    def get_orders(self, status: Optional[str] = None) -> list:
        """
        Fetches all orders from KDS.
        
        1. Calls GET /kds/orders endpoint
        2. Optionally filters by status
        
        Args:
            status: Filter by status (pending, in_progress, completed)
        
        Returns:
            list: Orders with items and status
        """
        params = {"status": status} if status else {}
        r = requests.get(
            f"{self.base_url}/kds/orders",
            params=params,
            timeout=5.0
        )
        r.raise_for_status()
        return r.json()
    
    def health_check(self) -> dict:
        """
        Checks KDS service health.
        
        Returns:
            dict: {status, service}
        """
        r = requests.get(f"{self.base_url}/kds/health", timeout=5.0)
        r.raise_for_status()
        return r.json()

def submit_order_to_kds(cart_items: list) -> dict | None:
    """
    Submits order to KDS display.
    
    1. Transforms cart items to KDS format
    2. Posts to /kds/order
    3. Returns order confirmation
    
    Args:
        cart_items: [{item_code, menu_name, quantity, price}, ...]
    
    Returns:
        dict: {order_id, status, item_count} or None on failure
    """
    try:
        kds_items = [
            {
                "item_code": item["item_code"],
                "name": item["menu_name"],
                "quantity": item["quantity"],
                "price": item.get("price", 0)
            }
            for item in cart_items
        ]
        
        r = requests.post(
            f"{KDS_BASE_URL}/kds/order",
            json={"items": kds_items},
            timeout=5.0
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def get_kds_orders(status: Optional[str] = None) -> list:
    """
    Gets all orders from KDS.
    
    1. Calls /kds/orders endpoint
    2. Returns list of orders
    
    Args:
        status: Optional filter (pending, in_progress, completed)
    
    Returns:
        list: Orders from KDS
    """
    params = {"status": status} if status else {}
    r = requests.get(
        f"{KDS_BASE_URL}/kds/orders",
        params=params,
        timeout=5.0
    )
    r.raise_for_status()
    return r.json()

def check_kds_health() -> bool:
    """
    Checks if KDS service is running.
    
    Returns:
        bool: True if healthy, False otherwise
    """
    try:
        r = requests.get(f"{KDS_BASE_URL}/kds/health", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False
