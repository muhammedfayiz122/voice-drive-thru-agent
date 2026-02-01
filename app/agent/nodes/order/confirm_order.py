from app.agent.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)

def confirm_order(state: AgentState) -> AgentState:
    """
    Displays order summary and asks user for confirmation.
    Sets response_text with order details and waits for user input.
    """
    logger.info("Generating order confirmation prompt.")
    
    order_items = state.get("order_items", [])
    if not order_items:
        state["response_text"] = "Sorry, there was an issue with your order. Please try again."
        state["expects_user_reply"] = False
        return state
    
    # Build spoken order summary
    item_phrases = []
    total = 0.0
    
    for item in order_items:
        name = item.get("menu_name", item.get("requested_name", "item"))
        qty = item.get("quantity", 1)
        price = item.get("price", 0)
        item_total = price * qty
        total += item_total
        
        if qty == 1:
            item_phrases.append(f"one {name} for {price} rupees")
        else:
            item_phrases.append(f"{qty} {name} for {item_total:.0f} rupees")
    
    # Join items naturally for speech
    if len(item_phrases) == 1:
        items_text = item_phrases[0]
    elif len(item_phrases) == 2:
        items_text = f"{item_phrases[0]} and {item_phrases[1]}"
    else:
        items_text = ", ".join(item_phrases[:-1]) + f", and {item_phrases[-1]}"
    
    state["response_text"] = (
        f"Okay, so that's {items_text}. "
        f"Your total comes to {total:.0f} rupees. "
        "Should I place this order?"
    )
    state["expects_user_reply"] = True
    
    state["final_order"] = {
        "items": order_items,
        "total": total
    }
    
    return state