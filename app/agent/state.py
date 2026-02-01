"""
Agent State.

1. ParsedItem - Item parsed from customer speech
2. CartItem - Validated item in cart
3. ModificationRequest - Request to modify/remove item
4. AgentState - Main state passed through graph
"""

from typing import TypedDict, List, Dict, Optional, Literal


class ParsedItem(TypedDict):
    """
    Item parsed from customer speech.
    
    1. name: Item name as spoken
    2. quantity: Number requested (default 1)
    """
    name: str
    quantity: int


class CartItem(TypedDict):
    """
    Validated item in cart.
    
    1. item_code: System identifier
    2. menu_name: Official menu name
    3. requested_name: What customer said
    4. quantity: Number of items
    5. price: Unit price
    6. item_total: quantity * price
    """
    item_code: str
    menu_name: str
    requested_name: str
    quantity: int
    price: float
    item_total: float


class ModificationRequest(TypedDict):
    """
    Request to modify or remove cart item.
    
    1. modification_target: Item to modify/remove
    2. item_name: Item name
    3. new_quantity: New amount (0 means remove)
    """
    modification_target: Optional[str]
    item_name: str
    new_quantity: int


class AgentState(TypedDict):
    """
    Main state passed through LangGraph.
    
    1. Input fields: user_input, conversation_history
    2. Intent fields: intent, confidence, parsed_items
    3. Cart fields: cart_items, cart_total
    4. Output fields: response_text, conversation_complete
    
    Note: State is managed externally in main loop, passed fresh each invoke.
    """
    # Input
    user_input: str
    conversation_history: List[Dict[str, str]]
    
    # Intent Analysis
    intent: Optional[str]
    confidence: Optional[float]
    parsed_items: List[ParsedItem]
    
    modifications: Optional[ModificationRequest] 
    
    # Cart (accumulated order)
    cart_items: List[CartItem]
    cart_total: float
    
    # Validation Results (current turn)
    validated_items: List[Dict]
    unavailable_items: List[str]
    
    # Response
    response_text: str
    conversation_complete: bool
    
    # Error
    error: Optional[str]