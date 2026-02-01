from pydantic import BaseModel
from typing import List

class OrderItemRequest(BaseModel):
    name: str
    quantity: int
    
class OrderRequest(BaseModel):
    item_code: str
    quantity: int
