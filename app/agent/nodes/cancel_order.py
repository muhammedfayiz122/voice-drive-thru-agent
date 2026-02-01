from app.agent.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)

def cancel_order_node(state: AgentState) -> AgentState:
    """
    Handles CANCEL_ORDER - clears cart and resets order.
    """
    logger.info("Cancelling order...")
    
    state["cart_items"] = []
    state["cart_total"] = 0.0
    state["response_text"] = "No problem, I've cancelled your order. Is there anything else I can help you with?"
    state["conversation_complete"] = False
    
    return state
