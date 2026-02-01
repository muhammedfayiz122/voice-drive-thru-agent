from app.agent.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)

def inventory_response(state: AgentState) -> AgentState:
    """
    """
    logger.info("Generating inventory response...")
    
    order_items = state.get("order_items", [])
    inventory_target = state.get("inventory_target", "that item")
    
    # No items found in validation
    if not order_items:
        state["response_text"] = (
            f"Sorry, I couldn't find {inventory_target} on our menu. "
            "Is there something else I can help you with?"
        )
        state["expects_user_reply"] = True
        return state
    
    return state