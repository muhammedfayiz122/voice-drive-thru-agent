from app.agent.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)

def repeat_order_node(state: AgentState) -> AgentState:
    """
    Handles REPEAT_ORDER - reads back current cart.
    """
    logger.info("Reading back order...")
    
    cart_items = state.get("cart_items", [])
    cart_total = state.get("cart_total", 0.0)
    
    if not cart_items:
        state["response_text"] = "You haven't ordered anything yet. What would you like?"
        state["conversation_complete"] = False
        return state
    
    # Build order summary
    item_parts = []
    for item in cart_items:
        if item["quantity"] == 1:
            item_parts.append(f"one {item['menu_name']}")
        else:
            item_parts.append(f"{item['quantity']} {item['menu_name']}")
    
    if len(item_parts) == 1:
        items_text = item_parts[0]
    elif len(item_parts) == 2:
        items_text = f"{item_parts[0]} and {item_parts[1]}"
    else:
        items_text = ", ".join(item_parts[:-1]) + f", and {item_parts[-1]}"
    
    state["response_text"] = f"So far you have {items_text}. That's {cart_total:.0f} rupees. Anything else?"
    state["conversation_complete"] = False
    
    return state
