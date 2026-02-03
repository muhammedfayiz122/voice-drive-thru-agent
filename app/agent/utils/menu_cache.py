"""
Menu cache - singleton cache for menu and inventory data.

-> Fetches from MCP Server at startup
-> Caches locally for instant access

1. Loads menu/inventory once at startup via MCP
2. Provides instant local lookups after initial fetch
3. Refresh available via reload()
"""

import time
import threading
from typing import Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MenuCache:
    """
    Cache for menu and inventory.
    1. Lazy initialization on first access
    2. Thread-safe
    3. Local fuzzy matching on cached data
    """
    
    _instance = None
    _lock = threading.Lock()
    
    _menu: list = []
    _inventory: dict = {}
    _last_refresh: float = 0
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def initialize(cls):
        """
        Initializes cache at startup from MCP server.
        1. Fetches menu from MCP → Legacy System
        2. Fetches inventory from MCP → Legacy System
        3. Marks cache as ready
        # NOTE: We call this once at app startup.
        """
        if cls._initialized:
            return
        
        cls._load_from_mcp()
        cls._initialized = True
        logger.info("MenuCache initialized from MCP server")
    
    @classmethod
    def _load_from_mcp(cls):
        """
        Loads cache from MCP server - proper architecture!
        1. Calls MCP /mcp/menu endpoint
        2. Calls MCP /mcp/inventory endpoint
        3. Normalizes and caches the data
        """
        from app.agent.utils.mcp_client import MCPClient
        
        try:
            client = MCPClient()
            
            # Fetch menu from MCP server
            raw_menu = client.get_menu()
            
            # Normalize menu item fields
            cls._menu = []
            for item in raw_menu:
                normalized = {
                    "item_code": item.get("item_code"),
                    "name": item.get("name"),
                    "category": item.get("category", "Other"),
                    # Handle both price and price_inr
                    "price": item.get("price") or item.get("price_inr", 0),
                }
                cls._menu.append(normalized)
            
            logger.info(f"Loaded {len(cls._menu)} menu items from MCP server")
            
            # Fetch inventory from MCP server
            cls._inventory = client.get_inventory()
            logger.info(f"Loaded inventory from MCP server")
            
            cls._last_refresh = time.time()
            
        except Exception as e:
            logger.error(f"Failed to load cache from MCP server: {e}")
            cls._menu = []
            cls._inventory = {}
    
    @classmethod
    def get_menu(cls) -> list:
        """
        Returns cached menu.
        1. Auto-initializes if needed
        2. Returns cached list instantly
        
        Returns:
            list: Menu items [{name, price, item_code, category}, ...]
        """
        if not cls._initialized:
            cls.initialize()
        return cls._menu
    
    @classmethod
    def get_inventory(cls) -> dict:
        """
        Returns cached inventory.
        1. Auto-initializes if needed
        2. Returns cached dict instantly
        
        Returns:
            dict: {stock_levels: {}, machines: {}}
        """
        if not cls._initialized:
            cls.initialize()
        return cls._inventory
    
    @classmethod
    def reload(cls):
        """
        Reloads cache from MCP server.
        # NOTE: Call this if menu/inventory has changed.
        """
        cls._load_from_mcp()
        logger.info("MenuCache reloaded from MCP server")
    
    @classmethod
    def match_item(cls, item_name: str) -> Optional[dict]:
        """
        Matches item name to menu using local fuzzy matching.
        1. Exact match (case-insensitive)
        2. Substring match
        3. Token overlap
        4. Fuzzy similarity
        # NOTE: All matching done locally - no MCP call.
        
        Args:
            item_name: customer's spoken item name
        Returns:
            dict: matched menu item or None
        """
        from app.mcp_server.validator import match_menu_item
        return match_menu_item(item_name, cls.get_menu())
    
    @classmethod
    def check_availability(cls, item_code: str) -> tuple[bool, str]:
        """
        Checks item availability from cached inventory.
        1. Checks stock level
        2. Checks machine status for ICE* items
        # NOTE: Uses cached inventory - no MCP call.
        
        Args:
            item_code: item code to check
        Returns:
            tuple: (is_available, reason)
        """
        from app.mcp_server.validator import check_inventory
        return check_inventory(item_code, cls.get_inventory())
    
    @classmethod
    def get_similar_items(cls, item_name: str, top_n: int = 2) -> list:
        """
        Gets similar items for suggestions from cache.
        1. Uses cached menu
        2. Computes similarity locally
        Note: No MCP call - instant response.
        
        Args:
            item_name: item to find similar items for
            top_n: number of suggestions
        Returns:
            list: similar menu items
        """
        from app.mcp_server.validator import get_similar_items
        return get_similar_items(item_name, cls.get_menu(), top_n)
    
    @classmethod
    def get_categories(cls) -> list:
        """
        Gets unique categories from cached menu.
        Returns:
            list: category names
        """
        categories = []
        for item in cls.get_menu():
            cat = item.get("category", "Other")
            if cat not in categories:
                categories.append(cat)
        return categories


# Convenience functions for direct import
def get_cached_menu() -> list:
    """Returns cached menu."""
    return MenuCache.get_menu()

def get_cached_inventory() -> dict:
    """Returns cached inventory."""
    return MenuCache.get_inventory()

def match_item_cached(item_name: str) -> Optional[dict]:
    """Matches item using cache."""
    return MenuCache.match_item(item_name)

def check_availability_cached(item_code: str) -> tuple[bool, str]:
    """Checks availability using cache."""
    return MenuCache.check_availability(item_code)
