from pydantic import BaseModel
from typing import List, Optional, Literal

class ParsedItem(BaseModel):
    name: str
    quantity: int

class IntentAnalysisResult(BaseModel):
    intent: Literal["GREETING", "ORDER", "INVENTORY_QUESTION", "INVALID"]
    confidence: float
    order_items: Optional[List[ParsedItem]]
    inventory_item: Optional[str]