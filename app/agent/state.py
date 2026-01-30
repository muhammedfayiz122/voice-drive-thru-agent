from typing import TypedDict

class AgentState(TypedDict):
    user_intent: str
    parsed_items: list
    inventory_result: dict
    confirmation_required: str
    final_order: dict
    response: str
    