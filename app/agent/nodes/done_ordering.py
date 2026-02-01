from app.agent.state import AgentState
from app.agent.utils.mcp_client import submit_order
from app.utils.logger import get_logger

logger = get_logger(__name__)

def done_ordering_node(state: AgentState) -> AgentState:
    """
    Handles DONE_ORDERING - submits order and gives total.
    """
    logger.info("Completing order...")
    
    cart_items = state.get("cart_items", [])
    cart_total = state.get("cart_total", 0.0)
    
    if not cart_items:
        state["response_text"] = "You haven't ordered anything yet. What would you like?"
        state["conversation_complete"] = False
        return state
    
    # Submit all items to MCP
    try:
        for item in cart_items:
            result = submit_order({
                "item_code": item["item_code"],
                "quantity": item["quantity"]
            })
            logger.info(f"Order submitted: {result}")
    except Exception as e:
        logger.error(f"Order submission failed: {e}")
        state["response_text"] = "Sorry, I had trouble placing your order. Let me try again."
        state["conversation_complete"] = False
        return state
    
    # Build confirmation response
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
    
    state["response_text"] = (
        f"Alright, that's {items_text}. "
        f"Your total is {cart_total:.0f} rupees. "
        "Please pull forward to the window. Thank you!"
    )
    state["conversation_complete"] = True
    
    return state
