from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class ParsedItem(BaseModel):
    name: str
    quantity: Optional[int] = Field(default=1, description="Quantity of items. Use 1 for inventory questions or when not specified.")

class IntentAnalysisResult(BaseModel):
    intent: Literal["GREETING", "ORDER", "INVENTORY_QUESTION", "INVALID"]
    confidence: float
    items: List[ParsedItem] = Field(default_factory=list, description="List of items mentioned. ALWAYS extract items for ORDER and INVENTORY_QUESTION intents.")