"""
Cancel Order Node - Handles CANCEL_ORDER intent.

1. Clears cart
2. Resets cart total
3. Offers to start over
"""

from app.agent.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)


def cancel_order_node(state: AgentState) -> dict:
    """
    Handles CANCEL_ORDER intent to clear order.
    
    1. Resets cart_items to empty list
    2. Resets cart_total to 0.0
    3. Returns polite cancellation message
    
    Args:
        state: Current agent state
    
    Returns:
        dict: Updated state with cleared cart
    """
    logger.info("Cancelling order...")
    
    state["cart_items"] = []
    state["cart_total"] = 0.0
    state["response_text"] = "No problem, I've cancelled your order. Is there anything else I can help you with?"
    state["conversation_complete"] = False
    
    return state
