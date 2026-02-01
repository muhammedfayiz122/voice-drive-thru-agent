from typing import TypedDict, List, Dict, Optional

class ParsedItem(TypedDict):
    name: str
    quantity: int

class AgentState(TypedDict):
    # User Input
    user_input: str

    # Intent Analysis (from LLM)
    intent: Optional[str]                # GREETING | ORDER | INVENTORY_QUESTION | INVALID
    confidence: Optional[float]
    parsed_items: List[ParsedItem]
    inventory_target: Optional[str]      # for inventory questions

    # Order Validation (from MCP)
    order_items: Optional[List[Dict]]    # Validated items with prices, availability
    all_items_available: Optional[bool]  # Quick check for routing
    unavailable_items: Optional[List[str]]  # Names of unavailable items

    # Final Order
    final_order: Optional[Dict]
    
    # Response Generation
    response_text: Optional[str]
    expects_user_reply: Optional[bool] = False
    
    # Error handling
    error: Optional[str]    
