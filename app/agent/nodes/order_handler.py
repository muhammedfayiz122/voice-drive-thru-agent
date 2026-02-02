"""
Order Handler Node - Handles ORDER and ADD_MORE intents.

Optimized: Uses MenuCache for instant local validation.
No MCP calls in request path.


1. Validates items against cached menu
2. Checks availability from cached inventory
3. Adds valid items to cart
4. Generates voice-friendly response with suggestions

# CRITICAL: No MCP calls in request path - must use MenuCache only!
# TODO: Call MCP -> for final validation at order submission time and distract user by saying "Let me double-check that for you".
# REVISE: fuzzy matching vs llm matching for item names.
"""

import time
from app.agent.state import AgentState
from app.agent.utils.menu_cache import MenuCache
from app.utils.logger import get_logger

logger = get_logger(__name__)

class OrderHandler:
    def __init__(self):
        pass
    
    # order_handler node
    def __call__(self, state: AgentState) -> AgentState:
        """
        handles |ORDER| and |ADD_MORE| intents.
        1. Extracts parsed_items from state
        2. Validates each item via MCP server
        3. Adds valid items to cart (updates quantity if exists)
        4. Generates response with suggestions for unavailable
        
        # REVISE: Generating response with LLM for more natural speech?
        # REVISE: Generating reponse logic
        
        Args:
            state: Current agent state with parsed_items, cart_items, cart_total
        Returns:
            dict: Updated state with cart_items, cart_total, response_text
        """
        total_start = time.perf_counter()
        logger.info("ORDER_HANDLER: Starting order processing")
        
        parsed_items = state.get("parsed_items", [])
        cart_items = state.get("cart_items", [])
        cart_total = state.get("cart_total", 0.0)
        
        # logger.info(f"ORDER_HANDLER: Parsed items count: {len(parsed_items)}")
        
        if not parsed_items:
            elapsed = (time.perf_counter() - total_start) * 1000
            # logger.info(f"ORDER_HANDLER: No items - returning early | Total: {elapsed:.2f}ms")
            return {
                "response_text": "I didn't catch what you'd like to order. Could you repeat that?",
                "conversation_complete": False
            }
        
        # Convert parsed items to list of dicts for MCP
        step_start = time.perf_counter()
        items_for_validation = self._prepare_items_for_validation(parsed_items)
        # logger.info(f"ORDER_HANDLER: [1] Prepare items | {(time.perf_counter() - step_start) * 1000:.2f}ms")
        
        # Validate items using CACHED menu (NO MCP CALL!)
        step_start = time.perf_counter()
        try:
            validated = self._validate_items_from_cache(items_for_validation)
            # logger.info(f"ORDER_HANDLER: [2] Cache validation | {(time.perf_counter() - step_start) * 1000:.2f}ms")
            # logger.info(f"ORDER_HANDLER: Validated items: {len(validated)}")
        except Exception as e:
            elapsed = (time.perf_counter() - total_start) * 1000
            logger.error(f"ORDER_HANDLER: Cache validation failed: {e} | Total: {elapsed:.2f}ms")
            return {
                "response_text": "Sorry, I'm having trouble checking our menu right now. Could you try again?",
                "conversation_complete": False
            }
        
        # Process results
        step_start = time.perf_counter()
        added_items, unavailable_items, cart_items, cart_total = self._process_validation_results(
            validated, cart_items
        )
        # logger.info(f"ORDER_HANDLER: [3] Process results | {(time.perf_counter() - step_start) * 1000:.2f}ms")
        # logger.info(f"ORDER_HANDLER: Added: {len(added_items)}, Unavailable: {len(unavailable_items)}")
        
        # Get suggestions for unavailable items
        step_start = time.perf_counter()
        suggestions = self._get_suggestions_for_unavailable(unavailable_items)
        # logger.info(f"ORDER_HANDLER: [4] Get suggestions | {(time.perf_counter() - step_start) * 1000:.2f}ms")
        
        # Generate response
        step_start = time.perf_counter()
        response = self._generate_order_response(added_items, unavailable_items, suggestions)
        # logger.info(f"ORDER_HANDLER: [5] Generate response | {(time.perf_counter() - step_start) * 1000:.2f}ms")
        
        total_elapsed = (time.perf_counter() - total_start) * 1000
        # logger.info(f"ORDER_HANDLER: ✓ COMPLETED | Total time: {total_elapsed:.2f}ms")
        logger.info("=" * 50)
        
        return {
            "cart_items": cart_items,
            "cart_total": cart_total,
            "validated_items": added_items,
            "unavailable_items": [u["name"] for u in unavailable_items],
            "response_text": response,
            "conversation_complete": False
        }


    def _prepare_items_for_validation(self, parsed_items: list) -> list:
        """
        Normalizing parsed items in specific format to send to MCP for validation.
        like:
        {
            "name": "Cheeseburger", 
            "quantity": 2
        }
        This fucntion ensures this format.
            
        Args:
            parsed_items: Items parser from user input (by LLM)
        
        Returns:
            list: Items formatted for validation
        """
        return [
            {
                "name": item.get("name") if isinstance(item, dict) else item.name, 
                "quantity": item.get("quantity", 1) if isinstance(item, dict) else getattr(item, "quantity", 1)
            }
            for item in parsed_items
        ]

    # Instead of calling MCP, we use MenuCache for validation
    def _validate_items_from_cache(self, items: list) -> list:
        """
        Validates items using cached menu
        # NOTE: NO MCP CALL - uses MenuCache only
        its actaully doing:
        1. Matches item name to menu using fuzzy matching
        2. Checks availability from cached inventory
        3. Returns validation result
        
        Args:
            items: List of {name, quantity}
        Returns:
            list: Validation results with found/available status
        """
        results = []
        
        for item in items:
            name = item.get("name", "")
            quantity = item.get("quantity", 1)
            
            # 1) Match against cached menu (fuzzy matching)
            matched = MenuCache.match_item(name)
            if not matched:
                results.append({
                    "requested_name": name,
                    "quantity": quantity,
                    "found": False,
                    "available": False,
                    "reason": "not on our menu"
                })
                continue
            
            # 2) Check availability from cached inventory
            available, reason = MenuCache.check_availability(matched["item_code"])
            results.append({
                "requested_name": name,
                "menu_name": matched["name"],
                "item_code": matched["item_code"],
                "price": matched.get("price", 0),
                "quantity": quantity,
                "found": True,
                "available": available,
                "reason": reason if not available else None
            })
        
        return results


    def _process_validation_results(self, validated: list, cart_items: list) -> tuple:
        """
        Processes MCP validation results.
        
        1. Separates valid/invalid items
        2. Updates or adds to cart
        3. Recalculates cart total
        
        Args:
            validated: Results from MCP validation
            cart_items: Current cart
        
        Returns:
            tuple: (added_items, unavailable_items, updated_cart, new_total)
        """
        added_items = []
        unavailable_items = []
        
        for item in validated:
            if item.get("found") and item.get("available"):
                cart_item = {
                    "item_code": item.get("item_code"),
                    "menu_name": item.get("menu_name"),
                    "requested_name": item.get("requested_name"),
                    "quantity": item.get("quantity", 1),
                    "price": item.get("price", 0),
                    "item_total": item.get("price", 0) * item.get("quantity", 1),
                }
                
                # Check if item already in cart - update quantity
                existing = next(
                    (
                        existing_cart_item for existing_cart_item in cart_items 
                        if existing_cart_item["item_code"] == cart_item["item_code"]
                    ),
                    None
                )
                if existing:
                    existing["quantity"] += cart_item["quantity"]
                    existing["item_total"] = existing["price"] * existing["quantity"]
                else:
                    cart_items.append(cart_item)
                
                added_items.append(cart_item)
            else:
                unavailable_items.append({
                    "name": item.get("requested_name"),
                    "reason": item.get("reason", "Not available")
                })
        
        # Recalculate total
        cart_total = sum(item["item_total"] for item in cart_items)
        
        return added_items, unavailable_items, cart_items, cart_total


    def _get_suggestions_for_unavailable(self, unavailable_items: list) -> dict:
        """
        Gets similar item suggestions using CACHED menu - NO MCP CALL!
        1. Uses MenuCache.get_similar_items()
        2. Maps each unavailable item to suggestions
        
        Args:
            unavailable_items: List of items not found/available
        Returns:
            dict: {item_name: [suggestion1, suggestion2, ...]}
        """
        if not unavailable_items:
            logger.info("ORDER_HANDLER: [4a] No unavailable items - skipping suggestions")
            return {}
        
        suggestions = {}
        try:
            step_start = time.perf_counter()
            for i, item in enumerate(unavailable_items):
                item_start = time.perf_counter()
                # Use cached menu for similarity - NO MCP CALL
                similar = MenuCache.get_similar_items(item["name"], top_n=2)
                if similar:
                    suggestions[item["name"]] = [similar_item["name"] for similar_item in similar]
                # logger.info(f"ORDER_HANDLER: [4a] Similar items for '{item['name']}' | {(time.perf_counter() - item_start) * 1000:.2f}ms")
            
            # logger.info(f"ORDER_HANDLER: [4] Total suggestions | {(time.perf_counter() - step_start) * 1000:.2f}ms")
        except Exception as e:
            logger.warning(f"ORDER_HANDLER: Could not get suggestions: {e}")
        
        return suggestions


    def _generate_order_response(self, added: list, unavailable: list, suggestions: dict) -> str:
        """
        Generates natural spoken response for order.
        1. Confirms added items
        2. Apologizes for unavailable with suggestions
        3. Asks for more items
        
        Args:
            added: successfully added items
            unavailable: items not available
            suggestions: similar items for unavailable
        Returns:
            str: final order status response
        """
        parts = []
        
        # Acknowledge added items
        if added:
            if len(added) == 1:
                item = added[0]
                parts.append(f"Got it, {item['quantity']} {item['menu_name']}")
            else:
                item_names = [f"{i['quantity']} {i['menu_name']}" for i in added]
                if len(item_names) == 2:
                    items_text = f"{item_names[0]} and {item_names[1]}"
                else:
                    items_text = ", ".join(item_names[:-1]) + f", and {item_names[-1]}"
                parts.append(f"Got it, {items_text}")
        
        # Mention unavailable with suggestions
        if unavailable:
            for item in unavailable:
                name = item["name"]
                reason = item.get("reason", "not available")
                
                if name in suggestions and suggestions[name]:
                    suggestion_text = " or ".join(suggestions[name][:2])
                    parts.append(f"Sorry, {name} is {reason}. How about {suggestion_text} instead?")
                else:
                    parts.append(f"Sorry, {name} is {reason}")
        
        # Ask for more
        if added or not unavailable:
            parts.append("Anything else?")
        elif unavailable and any(name in suggestions for name in [unavailable_item["name"] for unavailable_item in unavailable]):
            pass  # Already asked with suggestion
        else:
            parts.append("Would you like something else?")
        
        return " ".join(parts)
    
order_handler = OrderHandler()