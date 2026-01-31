from typing import TypedDict, List, Dict, Optional

class ParsedItem(TypedDict):
    name: str
    quantity: int

class AgentState(TypedDict):
    user_input: str

    intent: Optional[str]                # GREETING | ORDER | INVENTORY_QUESTION | INVALID
    parsed_items: List[ParsedItem]
    inventory_target: Optional[str]      # for inventory questions

    inventory_result: Dict[str, Dict]

    final_order: Optional[Dict]
    response: Optional[str]
    confidence: Optional[float]
    error: Optional[str]
