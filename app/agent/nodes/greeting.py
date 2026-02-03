"""
Greeting Node - Handles GREETING intent.

1. Returns welcome message
2. Asks what customer would like to order
"""

from app.agent.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)


def greeting_node(state: AgentState) -> dict:
    """
    Handles GREETING intent.
    
    1. Logs greeting generation
    2. Returns static welcome message
    3. Sets conversation_complete to False
    
    Note: Static response - no LLM call needed.
    
    Args:
        state: Current agent state
    
    Returns:
        dict: Updated state with response_text
    """
    logger.info("Generating greeting response...")
    
    state["response_text"] = "Hi there! Welcome to QuickBite. What can I get for you today?"
    state["conversation_complete"] = False
    
    return state
