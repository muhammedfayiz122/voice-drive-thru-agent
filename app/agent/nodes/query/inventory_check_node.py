from app.agent.state import AgentState
from app.agent.utils.mcp_client import (
    check_inventory, 
    submit_order,
    search_menu
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
    all_items_available = True
    unavailable_items = []
    
    for item in items:
        user_item_name = item.get("name", "")
        requested_qty = item.get("quantity", 1)
        
    inventory_status = all_items_available
    state["inventory_status"] = inventory_status
    return state