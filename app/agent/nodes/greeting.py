from app.agent.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)

def greeting_node(state: AgentState) -> AgentState:
    """
    Handles GREETING intent.
    Welcomes customer and asks for their order.
    """
    logger.info("Generating greeting response...")
    
    state["response_text"] = "Hi there! Welcome to QuickBite. What can I get for you today?"
    state["conversation_complete"] = False
    
    return state
