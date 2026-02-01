from app.agent.state import AgentState
from app.agent.utils.mcp_client import (
    check_inventory, 
    submit_order,
    validate_order_items
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

def inventory_check(state: AgentState) -> AgentState:
    """
    Checks the inventory for the requested items.
    
    Args:
        state (AgentState): The current state of the agent.
    Returns:
        AgentState: The updated state of the agent.
    """
    logger.info("Performing inventory check.")
    
    items = state.get("parsed_items", [])
    
    try:
        result = validate_order_items(items)
        logger.info(f"Inventory check result: {result}")
        state["all_items_available"] = result.get("all_available", False)
        state["order_items"] = result.get("results", [])
    except Exception as e:
        logger.error(f"Inventory check failed: {e}")
        state["all_items_available"] = False
        state["order_items"] = []
        state["error"] = "Inventory check failed."
    
    return state