"""
Modify handler node - handles MODIFY intent.

1. Changes quantity of existing cart item
2. Recalculates cart total
3. Reports change to customer
"""

from app.agent.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)


def modify_handler(state: AgentState) -> dict:
    """
    handles MODIFY intent for changing item quantities.
    1. Extracts target item from modifications
    2. Searches cart by menu_name or requested_name
    3. Updates quantity and item_total
    4. Recalculates cart_total
    
    Args:
        state: current agent state with modifications and cart_items
    Returns:
        dict: updated state with modified cart
    """
    logger.info("Processing modification...")
    
    # 1) Extract modifications and cart items from state
    
    modifications = state.get("modifications")
    cart_items = state.get("cart_items", [])
    
    # If no modifications provided , gives default resposnse
    if not modifications:
        state["response_text"] = "Which item would you like to change?"
        state["conversation_complete"] = False
        return state
    
    target = modifications.get("item_name", "").lower()
    new_qty = modifications.get("new_quantity", 1)
    
    # If no target item specified, asks for clarification
    if not target:
        state["response_text"] = "Which item would you like to change?"
        state["conversation_complete"] = False
        return state
    
    # 2) Find item in cart
    cart_matched_items = None
    for item in cart_items:
        if target in item["menu_name"].lower() or target in item["requested_name"].lower():
            cart_matched_items = item
            break
    
    if not cart_matched_items:
        state["response_text"] = f"I don't see {target} in your order. Would you like to add it?"
        state["conversation_complete"] = False
        return state
    
    # 3) Update quantity
    old_qty = cart_matched_items["quantity"]
    cart_matched_items["quantity"] = new_qty
    cart_matched_items["item_total"] = cart_matched_items["price"] * new_qty
    
    # 4) Recalculate total
    cart_total = sum(item["item_total"] for item in cart_items)
    
    state["cart_items"] = cart_items
    state["cart_total"] = cart_total
    state["response_text"] = f"Changed {cart_matched_items['menu_name']} from {old_qty} to {new_qty}. Anything else?"
    state["conversation_complete"] = False
    
    return state
