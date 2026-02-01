from app.agent.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)

def modify_handler(state: AgentState) -> AgentState:
    """
    Handles MODIFY intent - changing quantity of existing item.
    """
    logger.info("Processing modification...")
    
    modifications = state.get("modifications")
    cart_items = state.get("cart_items", [])
    
    if not modifications:
        state["response_text"] = "Which item would you like to change?"
        state["conversation_complete"] = False
        return state
    
    target = modifications.get("item_name", "").lower()
    new_qty = modifications.get("new_quantity", 1)
    
    if not target:
        state["response_text"] = "Which item would you like to change?"
        state["conversation_complete"] = False
        return state
    
    # Find item in cart
    found_item = None
    for item in cart_items:
        if target in item["menu_name"].lower() or target in item["requested_name"].lower():
            found_item = item
            break
    
    if not found_item:
        state["response_text"] = f"I don't see {target} in your order. Would you like to add it?"
        state["conversation_complete"] = False
        return state
    
    # Update quantity
    old_qty = found_item["quantity"]
    found_item["quantity"] = new_qty
    found_item["item_total"] = found_item["price"] * new_qty
    
    # Recalculate total
    cart_total = sum(item["item_total"] for item in cart_items)
    
    state["cart_items"] = cart_items
    state["cart_total"] = cart_total
    state["response_text"] = f"Changed {found_item['menu_name']} from {old_qty} to {new_qty}. Anything else?"
    state["conversation_complete"] = False
    
    return state
