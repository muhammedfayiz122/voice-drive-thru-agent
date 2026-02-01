from app.agent.state import AgentState
from app.agent.utils.mcp_client import validate_order_items
from app.utils.logger import get_logger

logger = get_logger(__name__)

def inventory_query_node(state: AgentState) -> AgentState:
    """
    Handles INVENTORY_QUESTION - checks availability of items.
    """
    logger.info("Processing inventory query...")
    
    parsed_items = state.get("parsed_items", [])
    
    # If no items parsed, check modifications for query item
    if not parsed_items:
        modifications = state.get("modifications")
        if modifications and modifications.get("item_name"):
            parsed_items = [{"name": modifications["item_name"], "quantity": 1}]
    
    if not parsed_items:
        state["response_text"] = "What item would you like me to check?"
        state["conversation_complete"] = False
        return state
    
    # Convert to validation format
    items_for_validation = [
        {"name": item.get("name") if isinstance(item, dict) else item.name, 
         "quantity": 1}
        for item in parsed_items
    ]
    
    try:
        result = validate_order_items(items_for_validation)
        validated = result.get("results", [])
        logger.info(f"Inventory check result: {result}")
    except Exception as e:
        logger.error(f"Inventory check failed: {e}")
        state["response_text"] = "Sorry, I'm having trouble checking that right now."
        state["conversation_complete"] = False
        return state
    
    # Build response
    available = []
    not_available = []
    not_found = []
    
    for item in validated:
        name = item.get("menu_name") or item.get("requested_name")
        if not item.get("found"):
            not_found.append(item.get("requested_name"))
        elif item.get("available"):
            available.append(name)
        else:
            not_available.append((name, item.get("reason", "unavailable")))
    
    # Generate response
    parts = []
    
    if available:
        if len(available) == 1:
            parts.append(f"Yes, we have {available[0]}")
        else:
            parts.append(f"Yes, we have {', '.join(available)}")
    
    if not_available:
        for name, reason in not_available:
            parts.append(f"Sorry, {name} is {reason}")
    
    if not_found:
        for name in not_found:
            parts.append(f"I don't see {name} on our menu")
    
    cart_items = state.get("cart_items", [])
    if cart_items:
        parts.append("Would you like to add anything to your order?")
    else:
        parts.append("Would you like to order something?")
    
    state["response_text"] = ". ".join(parts)
    state["conversation_complete"] = False
    
    return state
