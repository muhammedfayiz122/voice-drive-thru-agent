"""
Remove Handler Node - Handles REMOVE intent.

1. Removes item from cart
2. Recalculates cart total
3. Reports removal to customer
"""

from app.agent.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)


def remove_handler(state: AgentState) -> dict:
    """
    handles REMOVE intent for removing cart items.
    1. Extracts target item from modifications
    2. Searches cart by menu_name or requested_name
    3. Removes matching item from cart
    4. Recalculates cart_total
    
    Args:
        state: current agent state with modifications and cart_items
    Returns:
        dict: updated state with item removed
    """
    logger.info("Processing removal...")
    
    modifications = state.get("modifications")
    cart_items = state.get("cart_items", [])

    # If user intended to REMOVE but modifications details missing (maybe LLM parsing issue or user vague)
    if not modifications:
        state["response_text"] = "Which item would you like to remove?"
        state["conversation_complete"] = False
        return state
    
    # If user intended to REMOVE but not mentioned items name
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
    
    # If no item was removed / if no item matched to remove from cart
    if len(cart_items) == original_count:
        state["response_text"] = f"I don't see {target} in your order."
        state["conversation_complete"] = False
        return state
    
    # Recalculate total
    cart_total = sum(item["item_total"] for item in cart_items)
    
    state["cart_items"] = cart_items
    state["cart_total"] = cart_total
    
    # if cart still has items after removal
    if cart_items:
        state["response_text"] = f"Removed {removed_name}. Anything else?"
    
    # if cart is now empty
    else:
        state["response_text"] = f"Removed {removed_name}. Your order is now empty. What would you like to order?"
    
    state["conversation_complete"] = False
    
    return state
