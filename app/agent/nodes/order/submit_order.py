from app.agent.state import AgentState
from app.utils.logger import get_logger
from app.agent.utils.mcp_client import submit_order

logger = get_logger(__name__)

def submit_order_node(state: AgentState) -> AgentState:
    """
    Submits the confirmed order to the MCP server.
    All-or-nothing: entire order succeeds or fails together.
    """
    logger.info("Submitting order to MCP server.")
    
    final_order = state.get("final_order")
    order_items = final_order.get("items", []) if final_order else state.get("order_items", [])
    
    if not order_items:
        state["response_text"] = "Sorry, something went wrong with your order. Please try again."
        state["expects_user_reply"] = False
        return state
    
    # Submit all items - fail entire order if any item fails
    try:
        for item in order_items:
            item_code = item.get("item_code")
            quantity = item.get("quantity", 1)
            
            result = submit_order({"item_code": item_code, "quantity": quantity})
            logger.info(f"Order item submitted: {result}")
        
        # All items succeeded
        total = final_order.get("total", 0) if final_order else 0
        state["response_text"] = (
            f"Your order has been placed successfully. "
            f"Your total is {total:.0f} rupees. "
            "Please drive to the next window. Thank you!"
        )
        state["expects_user_reply"] = False
        
    except Exception as e:
        logger.error(f"Order submission failed: {e}")
        state["response_text"] = (
            "Sorry, I couldn't place your order right now. "
            "Please try again or speak to our staff at the window."
        )
        state["expects_user_reply"] = False
    
    return state