from app.agent.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)

def unclear_handler(state: AgentState) -> AgentState:
    """
    Handles UNCLEAR intent - asks for clarification.
    """
    logger.info("Handling unclear input...")
    
    cart_items = state.get("cart_items", [])
    
    if cart_items:
        state["response_text"] = "Sorry, I didn't catch that. Would you like to add anything else or complete your order?"
    else:
        state["response_text"] = "Sorry, I didn't understand. What would you like to order today?"
    
    state["conversation_complete"] = False
    
    return state
