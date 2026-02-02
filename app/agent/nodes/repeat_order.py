"""
Repeat order node - handles REPEAT_ORDER intent.
1. Reads back current cart items
2. Reports running total
3. Asks if customer wants more
"""

from app.agent.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)


def repeat_order_node(state: AgentState) -> dict:
    """
    Handles REPEAT_ORDER intent to read back order.
    1. Checks if cart has items
    2. Formats items as natural speech
    3. Reports current total
    
    Args:
        state: current agent state with cart_items and cart_total
    Returns:
        dict: updated state with order summary
    """
    logger.info("Reading back order...")
    
    cart_items = state.get("cart_items", [])
    cart_total = state.get("cart_total", 0.0)
    
    # 1) Check if cart has items
    if not cart_items:
        state["response_text"] = "You haven't ordered anything yet. What would you like?"
        state["conversation_complete"] = False
        return state
    
    # 2) Build order summary
    response_items = []
    for item in cart_items:
        if item["quantity"] == 1:
            response_items.append(f"one {item['menu_name']}")
        else:
            response_items.append(f"{item['quantity']} {item['menu_name']}")
    
    if len(response_items) == 1:
        items_text = response_items[0]
    elif len(response_items) == 2:
        items_text = f"{response_items[0]} and {response_items[1]}"
    else:
        items_text = ", ".join(response_items[:-1]) + f", and {response_items[-1]}"
    
    # 3) Set response text
    state["response_text"] = f"So far you have {items_text}. That's {cart_total:.0f} rupees. Anything else?"
    state["conversation_complete"] = False
    
    return state
