"""
Intent Router - Routes to appropriate handler based on classified intent.

1. Receives classified intent from state
2. Maps intent to node name
3. Returns node name for graph routing
"""

from app.agent.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)


def intent_router(state: AgentState) -> str:
    """
    Routes to appropriate node based on intent.
    
    1. Extracts intent from state
    2. Looks up corresponding node in routing map
    3. Falls back to 'unclear' for unknown intents
    
    Args:
        state: Current agent state with intent field
    
    Returns:
        str: Node name to route to
    """
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
        "SHOW_MENU": "show_menu",
        "UNCLEAR": "unclear",
    }
    
    return routing.get(intent, "unclear")