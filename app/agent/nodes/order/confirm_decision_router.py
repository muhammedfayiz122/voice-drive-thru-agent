from app.agent.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)

def confirm_decision_router(state: AgentState) -> str:
    """
    Routes based on user's confirmation response.
    Expects user_input to contain yes/no response.
    """
    user_input = state.get("user_input", "").lower().strip()
    
    # Positive confirmations
    confirm_phrases = ["yes", "yeah", "yep", "sure", "okay", "ok", "confirm", "go ahead", "place it", "do it"]
    
    # Negative/cancel phrases
    cancel_phrases = ["no", "nope", "cancel", "nevermind", "never mind", "stop", "don't", "forget it"]
    
    for phrase in confirm_phrases:
        if phrase in user_input:
            logger.info("User confirmed the order.")
            return "confirm"
    
    for phrase in cancel_phrases:
        if phrase in user_input:
            logger.info("User cancelled the order.")
            return "cancel"
    
    logger.info("User response unclear, asking again.")
    return "invalid"