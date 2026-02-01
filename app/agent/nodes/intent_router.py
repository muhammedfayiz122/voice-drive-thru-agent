from app.agent.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)

def intent_router(state: AgentState) -> str:
    """Routes to appropriate node based on intent."""
    intent = state.get("intent", "UNCLEAR")
    
    logger.info(f"Routing intent: {intent}")
    
    routing = {
        "GREETING": "greeting",
        "ORDER": "order",
        "ADD_MORE": "order",           # Same handler as ORDER
        "MODIFY": "modify",
        "REMOVE": "remove",
        "DONE_ORDERING": "done",
        "CANCEL_ORDER": "cancel",
        "INVENTORY_QUESTION": "inventory",
        "REPEAT_ORDER": "repeat",
        "UNCLEAR": "unclear",
    }
    
    return routing.get(intent, "unclear")