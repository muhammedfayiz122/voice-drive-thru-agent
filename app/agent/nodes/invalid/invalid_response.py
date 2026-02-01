from app.agent.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)

def invalid_response(state: AgentState) -> AgentState:
    """
    Handle invalid responses in the agent's workflow.
    Args:
        state (AgentState): The current state of the agent.
    Returns:
        AgentState: The updated state of the agent.
    """
    logger.info("Handling invalid response.")
    state["expects_user_reply"] = False
    state["response_text"] = "Sorry, I didn't catch that. What can I get for you today?"
    return state
