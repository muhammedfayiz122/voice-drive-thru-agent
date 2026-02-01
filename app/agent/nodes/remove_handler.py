from app.agent.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)

def remove_handler(state: AgentState) -> AgentState:
    """
    Handles REMOVE intent - removing item from cart.
    """
    logger.info("Processing removal...")
    
    modifications = state.get("modifications")
    cart_items = state.get("cart_items", [])
    
    if not modifications:
        state["response_text"] = "Which item would you like to remove?"
        state["conversation_complete"] = False
        return state
    
    target = modifications.get("item_name", "").lower()
    
    if not target:
        state["response_text"] = "Which item would you like to remove?"
        state["conversation_complete"] = False
        return state
    
    # Find and remove item
    original_count = len(cart_items)
    removed_name = None
    
    for i, item in enumerate(cart_items):
        if target in item["menu_name"].lower() or target in item["requested_name"].lower():
            removed_name = item["menu_name"]
            cart_items.pop(i)
            break
    
    if len(cart_items) == original_count:
        state["response_text"] = f"I don't see {target} in your order."
        state["conversation_complete"] = False
        return state
    
    # Recalculate total
    cart_total = sum(item["item_total"] for item in cart_items)
    
    state["cart_items"] = cart_items
    state["cart_total"] = cart_total
    
    if cart_items:
        state["response_text"] = f"Removed {removed_name}. Anything else?"
    else:
        state["response_text"] = f"Removed {removed_name}. Your order is now empty. What would you like to order?"
    
    state["conversation_complete"] = False
    
    return state
