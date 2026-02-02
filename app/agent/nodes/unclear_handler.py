"""
Unclear Handler Node - Handles UNCLEAR intent.

1. Provides polite clarification request
2. Context-aware based on cart state (middle of order vs new)
"""

from app.agent.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)

def unclear_handler(state: AgentState) -> dict:
    """
    Handles UNCLEAR intent for unrecognized input.
    
    1. Checks if cart has items (mid-order)
    2. Returns context-appropriate clarification
    3. Guides customer back to ordering flow
    
    Args:
        state: current agent state
    Returns:
        dict: updated state with clarification request
    """
    logger.info("Handling unclear input...")
    
    cart_items = state.get("cart_items", [])
    if cart_items:
        state["response_text"] = "Sorry, I didn't catch that. Would you like to add anything else or complete your order?"
    else:
        state["response_text"] = "Sorry, I didn't understand. What would you like to order today?"
    state["conversation_complete"] = False
    return state
