"""
Done ordering node - handles DONE_ORDERING intent.

-> Responds immediately, submits order in background.

1. Reads back order and total
2. Marks conversation complete
3. Fires off order submission asynchronously (non-blocking)
"""

import threading
from app.agent.state import AgentState
from app.agent.utils.mcp_client import submit_order
from app.agent.utils.kds_client import submit_order_to_kds
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _submit_order_background(cart_items: list):
    """
    Submits order to MCP and KDS in background thread.
    # NOTE: Non-blocking - voice response already sent to customer.
    1) Submit order to MCP
    2) Submit order to KDS
    """
    try:
        # Submit to MCP
        for item in cart_items:
            result = submit_order({
                "item_code": item["item_code"],
                "quantity": item["quantity"]
            })
            logger.info(f"Background order submitted: {result}")
        
        # Send to KDS
        kds_result = submit_order_to_kds(cart_items)
        if kds_result:
            logger.info(f"Order sent to KDS: {kds_result['order_id']}")
        else:
            logger.warning("Could not send to KDS")
    except Exception as e:
        logger.error(f"Background order submission failed: {e}")


def done_ordering_node(state: AgentState) -> dict:
    """
    Handles DONE_ORDERING intent to complete order.
    
    -> Responds immediately, submits in background.
    
    1. Validates cart is not empty
    2. Builds confirmation response with items and total
    3. Fires background thread for MCP/KDS (like fire and forget)
    4. Returns immediately with confirmation
    
    Args:
        state: current agent state with cart_items
    Returns:
        dict: updated state with confirmation and total
    """
    logger.info("Completing order...")
    
    # 1) Validate cart not empty
    cart_items = state.get("cart_items", [])
    cart_total = state.get("cart_total", 0.0)
    if not cart_items:
        return {
            "response_text": "You haven't ordered anything yet. What would you like?",
            "conversation_complete": False
        }
    
    # 2) Fire background submission (non-blocking!)
    thread = threading.Thread(
        target=_submit_order_background,
        args=(cart_items.copy(),),
        daemon=True
    )
    thread.start()
    logger.info("Order submission started in background")
    
    # 3) Build confirmation response immediately
    order_item_response = []
    for item in cart_items:
        if item["quantity"] == 1:
            order_item_response.append(f"one {item['menu_name']}")
        else:
            order_item_response.append(f"{item['quantity']} {item['menu_name']}")
    
    if len(order_item_response) == 1:
        items_text = order_item_response[0]
    elif len(order_item_response) == 2:
        items_text = f"{order_item_response[0]} and {order_item_response[1]}"
    else:
        items_text = ", ".join(order_item_response[:-1]) + f", and {order_item_response[-1]}"
    
    return {
        "response_text": (
            f"Alright, that's {items_text}. "
            f"Your total is {cart_total:.0f} rupees. "
            "Please pull forward to the window. Thank you!"
        ),
        "conversation_complete": True,
        # Reset cart after order completion
        "cart_items": [],
        "cart_total": 0.0 
    }
