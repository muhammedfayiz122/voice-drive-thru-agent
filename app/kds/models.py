"""
KDS Data Models - Order representation for kitchen display.

1. OrderItem - Individual item in an order
2. Order - Complete order with items and status
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from enum import Enum


class OrderStatus(Enum):
    """Order status in kitchen workflow."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class OrderItem:
    """Single item in an order."""
    item_code: str
    name: str
    quantity: int
    price: float = 0.0


@dataclass
class Order:
    """Complete order for KDS display."""
    order_id: str
    items: List[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    total: float = 0.0
    
    def calculate_total(self):
        """Calculate order total from items."""
        self.total = sum(item.price * item.quantity for item in self.items)
        return self.total
