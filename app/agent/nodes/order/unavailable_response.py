from app.agent.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)

def unavailable_response(state: AgentState) -> AgentState:
    """
    """
    logger.info("Generating inventory response...")
    
    order_items = state.get("order_items", [])
    inventory_target = state.get("inventory_target", "that item")
    
    # No items found in validation
    if not order_items:
        state["response_text"] = (
            f"Sorry, I couldn't find {inventory_target} on our menu. "
            "Is there something else I can help you with?"
        )
        state["expects_user_reply"] = True
        return state
    
    # Separate found vs not found, available vs unavailable
    available_items = []
    unavailable_items = []
    not_found_items = []
    
    for item in order_items:
        # Check if item was found on menu
        if not item.get("found", False):
            not_found_items.append(item.get("requested_name", "item"))
            continue
        
        # Use menu_name (official name), not requested_name
        menu_name = item.get("menu_name")
        price = item.get("price")
        
        if item.get("available", False):
            if price:
                available_items.append(f"{menu_name} (₹{price})")
            else:
                available_items.append(menu_name)
        else:
            reason = item.get("reason", "")
            unavailable_items.append((menu_name, reason))
    
    # Build response
    response_parts = []
    
    if available_items:
        if len(available_items) == 1:
            response_parts.append(f"Yes, we have {available_items[0]}.")
        else:
            items_text = ", ".join(available_items)
            response_parts.append(f"Yes, we have: {items_text}.")
    
    if unavailable_items:
        for menu_name, reason in unavailable_items:
            if "machine" in reason.lower():
                response_parts.append(f"Sorry, {menu_name} isn't available - {reason}.")
            else:
                response_parts.append(f"Sorry, we're out of {menu_name}.")
    
    if not_found_items:
        items_text = ", ".join(not_found_items)
        response_parts.append(f"I couldn't find {items_text} on our menu.")
    
    if available_items:
        response_parts.append("Would you like to order?")
    
    state["response_text"] = " ".join(response_parts)
    state["expects_user_reply"] = True
    return state