from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class ParsedItem(BaseModel):
    name: str = Field(description="Item name as spoken by customer")
    quantity: int = Field(default=1, description="Quantity requested, default 1")

class IntentAnalysisResult(BaseModel):
    intent: Literal[
        "GREETING",           # "hi", "hello"
        "ORDER",              # "I want 2 burgers"
        "ADD_MORE",           # "also add fries", "and a coke"
        "MODIFY",             # "change fries to large", "make it 3 burgers"
        "REMOVE",             # "remove the fries", "cancel the burger"
        "DONE_ORDERING",      # "that's all", "that's it", "nothing else"
        "CANCEL_ORDER",       # "cancel everything", "nevermind"
        "INVENTORY_QUESTION", # "do you have ice cream?"
        "REPEAT_ORDER",       # "what did I order?", "read my order"
        "UNCLEAR"             # Ambiguous or off-topic
    ]
    confidence: float = Field(ge=0, le=1)
    
    # For ORDER, ADD_MORE
    items: List[ParsedItem] = Field(default_factory=list)
    
    # For MODIFY, REMOVE
    target_item: Optional[str] = Field(default=None, description="Item to modify/remove")
    new_quantity: Optional[int] = Field(default=None, description="New quantity for MODIFY")
    
    # For INVENTORY_QUESTION
    query_item: Optional[str] = Field(default=None)