from app.agent.state import AgentState
from app.agent.utils.mcp_client import validate_order_items
from app.utils.logger import get_logger

logger = get_logger(__name__)

def order_handler(state: AgentState) -> AgentState:
    """
    Handles ORDER and ADD_MORE intents.
    Validates items via MCP, adds valid items to cart.
    """
    logger.info("Processing order...")
    
    parsed_items = state.get("parsed_items", [])
    cart_items = state.get("cart_items", [])
    cart_total = state.get("cart_total", 0.0)
    
    if not parsed_items:
        state["response_text"] = "I didn't catch what you'd like to order. Could you repeat that?"
        state["conversation_complete"] = False
        return state
    
    # Convert parsed items to list of dicts for MCP
    items_for_validation = [
        {"name": item.get("name") if isinstance(item, dict) else item.name, 
         "quantity": item.get("quantity", 1) if isinstance(item, dict) else getattr(item, "quantity", 1)}
        for item in parsed_items
    ]
    
    # Validate items via MCP
    try:
        result = validate_order_items(items_for_validation)
        validated = result.get("results", [])
        logger.info(f"MCP validation result: {result}")
    except Exception as e:
        logger.error(f"MCP validation failed: {e}")
        state["response_text"] = "Sorry, I'm having trouble checking our menu right now. Could you try again?"
        state["conversation_complete"] = False
        return state
    
    # Process results
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
            existing = next((c for c in cart_items if c["item_code"] == cart_item["item_code"]), None)
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
    
    # Generate response
    response = _generate_order_response(added_items, unavailable_items)
    
    state["cart_items"] = cart_items
    state["cart_total"] = cart_total
    state["validated_items"] = added_items
    state["unavailable_items"] = [u["name"] for u in unavailable_items]
    state["response_text"] = response
    state["conversation_complete"] = False
    
    return state

def _generate_order_response(added: list, unavailable: list) -> str:
    """Generate natural spoken response for order."""
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
    
    # Mention unavailable
    if unavailable:
        if len(unavailable) == 1:
            parts.append(f"Sorry, {unavailable[0]['name']} is not available right now")
        else:
            names = [u["name"] for u in unavailable]
            parts.append(f"Sorry, {' and '.join(names)} are not available right now")
    
    # Ask for more
    if added or not unavailable:
        parts.append("Anything else?")
    else:
        parts.append("Would you like something else instead?")
    
    return ". ".join(parts)
