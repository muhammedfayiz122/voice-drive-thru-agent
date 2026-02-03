"""
Inventory Query Node - Handles INVENTORY_QUESTION intent.

# NOTE: Uses MenuCache for instant response.
# NO MCP CALLS in request path.

1. Checks item availability from cached data
2. Reports whether items are available
3. Suggests similar items if not found
"""

from app.agent.state import AgentState
from app.agent.utils.menu_cache import MenuCache
from app.utils.logger import get_logger

logger = get_logger(__name__)

class InventoryQueryNode:
    def __init__(self):
        pass
    
    
    def __call__(self, state: AgentState) -> dict:
        """
        handles INVENTORY_QUESTION intent.
        
        # NOTE: Uses cached menu/inventory 
        # NO MCP CALLS in request path.
        
        1. Extracts query item from parsed_items or modifications
        2. Validates using MenuCache
        3. Reports availability with suggestions
        4. Asks if customer wants to order
        
        Args:
            state: current agent state
        Returns:
            dict: updated state with response_text
        """
        logger.info("Processing inventory query...")
        
        parsed_items = state.get("parsed_items", [])
        # If no items parsed, check modifications for query item
        if not parsed_items:
            modifications = state.get("modifications")
            if modifications and modifications.get("item_name"):
                parsed_items = [{"name": modifications["item_name"], "quantity": 1}]
        
        if not parsed_items:
            return {
                "response_text": "What item would you like me to check?",
                "conversation_complete": False
            }
        
        # Making data ready for sending to MCP for validation
        items_for_validation = self._prepare_items(parsed_items)
        
        try:
            # Validate using cached menu/inventory (no MCP calls)
            validated = self._validate_items_from_cache(items_for_validation)
            logger.info(f"Inventory check result: {validated}")
        except Exception as e:
            logger.error(f"Inventory check failed: {e}")
            return {
                "response_text": "Sorry, I'm having trouble checking that right now.",
                "conversation_complete": False
            }
        
        # Build response with suggestions
        response = self._build_inventory_response(validated, state.get("cart_items", []))
        
        return {
            "response_text": response,
            "conversation_complete": False
        }


    def _prepare_items(self, parsed_items: list) -> list:
        """
        Prepares items for validation.
        
        1. Handles dict and object formats
        2. Sets quantity to 1 for availability check
        
        Args:
            parsed_items: Items from state
        
        Returns:
            list: Items formatted for validation
        """
        return [
            {
                "name": item.get("name") if isinstance(item, dict) else item.name, 
                "quantity": 1
            }
            for item in parsed_items
        ]


    def _validate_items_from_cache(self, items: list) -> list:
        """
        Validates items using cached menu - NO MCP CALL!
        
        1. Matches item name to menu using fuzzy matching
        2. Checks availability from cached inventory
        
        Args:
            items: List of {name, quantity}
        
        Returns:
            list: Validation results
        """
        results = []
        
        for item in items:
            name = item.get("name", "")
            
            # Match against cached menu (fuzzy matching)
            matched = MenuCache.match_item(name)
            
            if not matched:
                results.append({
                    "requested_name": name,
                    "found": False,
                    "available": False,
                    "reason": "not on our menu"
                })
                continue
            
            # Check availability from cached inventory
            available, reason = MenuCache.check_availability(matched["item_code"])
            
            results.append({
                "requested_name": name,
                "menu_name": matched["name"],
                "item_code": matched["item_code"],
                "found": True,
                "available": available,
                "reason": reason if not available else None
            })
        
        return results
    
    
    def _build_inventory_response(self, validated: list, cart_items: list) -> str:
        """
        builds response for inventory query.
        1. Reports available items
        2. Reports unavailable with reason
        3. Suggests similar items for not found
        4. Asks follow-up question
        
        Args:
            validated: Validation results
            cart_items: Current cart for context
        
        Returns:
            str: deterministic response , tailored for inventory query
        """
        available = []
        not_available = []
        not_found = []
        
        for item in validated:
            name = item.get("menu_name") or item.get("requested_name")
            if not item.get("found"):
                not_found.append(item.get("requested_name"))
            elif item.get("available"):
                available.append(name)
            else:
                not_available.append((name, item.get("reason", "unavailable")))
        
        parts = [] 
        if available:
            if len(available) == 1:
                parts.append(f"Yes, we have {available[0]}")
            else:
                parts.append(f"Yes, we have {', '.join(available)}")
        
        if not_available:
            for name, reason in not_available:
                parts.append(f"Sorry, {reason}")
        
        if not_found:
            # Get suggestions using cache (no MCP calls)
            suggestions = self._get_suggestions(not_found)
            for name in not_found:
                if name in suggestions and suggestions[name]:
                    suggestion_text = " or ".join(suggestions[name][:2])
                    parts.append(f"I don't have {name}, but we do have {suggestion_text}")
                else:
                    parts.append(f"I don't see {name} on our menu")
        
        # Follow-up question
        if cart_items:
            parts.append("Would you like to add anything to your order?")
        else:
            parts.append("Would you like to order something?")
        
        return " ".join(parts)


    def _get_suggestions(self, not_found_items: list) -> dict:
        """
        Gets similar item suggestions using cache (no MCP calls)
        1. Uses MenuCache.get_similar_items()
        2. Finds similar items for each
        
        Args:
            not_found_items: Items not found in menu
        Returns:
            dict: {item_name: [suggestion1, suggestion2]}
        """
        suggestions = {}
        try:
            for name in not_found_items:
                similar = MenuCache.get_similar_items(name, top_n=2)
                if similar:
                    suggestions[name] = [s["name"] for s in similar]
        except Exception as e:
            logger.warning(f"Could not get suggestions: {e}")
        
        return suggestions

inventory_query_node = InventoryQueryNode()