from typing import TypedDict, List, Dict, Optional, Literal

class ParsedItem(TypedDict):
    name: str
    quantity: int

class CartItem(TypedDict):
    item_code: str
    menu_name: str
    requested_name: str
    quantity: int
    price: float
    item_total: float

class ModificationRequest(TypedDict):
    modification_target: Optional[str]    # For MODIFY/REMOVE - which item to change
    item_name: str
    new_quantity: int  # 0 means remove

class AgentState(TypedDict):
    # Input
    user_input: str
    conversation_history: List[Dict[str, str]]  # [{"role": "user/agent", "content": "..."}]
    
    # Intent Analysis
    intent: Optional[str]
    confidence: Optional[float]
    parsed_items: List[ParsedItem]       # Items from current utterance
    
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