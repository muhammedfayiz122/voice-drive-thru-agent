"""
KDS Order Store - Thread-safe order storage with signals.

1. Manages order queue
2. Provides thread-safe access for Qt and FastAPI
3. Emits signals when orders change
"""

from typing import Dict, List, Optional
from threading import Lock
from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime
import uuid

from app.kds.models import Order, OrderItem, OrderStatus


class OrderStore(QObject):
    """
    Thread-safe order storage with Qt signals.
    
    Signals:
        order_added: Emitted when new order arrives
        order_updated: Emitted when order status changes
    """
    
    order_added = pyqtSignal(str)  # order_id
    order_updated = pyqtSignal(str)  # order_id
    
    def __init__(self):
        super().__init__()
        self._orders: Dict[str, Order] = {}
        self._lock = Lock()
    
    def add_order(self, items: List[dict]) -> str:
        """
        Add new order to the store.
        
        Args:
            items: List of {item_code, name, quantity, price}
        
        Returns:
            order_id: Generated order ID
        """
        order_id = f"ORD-{datetime.now().strftime('%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        
        order_items = [
            OrderItem(
                item_code=item.get("item_code", ""),
                name=item.get("name", "Unknown"),
                quantity=item.get("quantity", 1),
                price=item.get("price", 0.0)
            )
            for item in items
        ]
        
        order = Order(
            order_id=order_id,
            items=order_items,
            status=OrderStatus.PENDING
        )
        order.calculate_total()
        
        with self._lock:
            self._orders[order_id] = order
        
        self.order_added.emit(order_id)
        return order_id
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        with self._lock:
            return self._orders.get(order_id)
    
    def get_all_orders(self) -> List[Order]:
        """Get all orders."""
        with self._lock:
            return list(self._orders.values())
    
    def get_pending_orders(self) -> List[Order]:
        """Get orders with PENDING status."""
        with self._lock:
            return [o for o in self._orders.values() if o.status == OrderStatus.PENDING]
    
    def update_status(self, order_id: str, status: OrderStatus) -> bool:
        """Update order status."""
        with self._lock:
            if order_id in self._orders:
                self._orders[order_id].status = status
                self.order_updated.emit(order_id)
                return True
        return False
    
    def clear_completed(self):
        """Remove completed orders."""
        with self._lock:
            self._orders = {
                k: v for k, v in self._orders.items() 
                if v.status != OrderStatus.COMPLETED
            }


# Global singleton instance
_store_instance: Optional[OrderStore] = None


def get_order_store() -> OrderStore:
    """Get or create global order store instance."""
    global _store_instance
    if _store_instance is None:
        _store_instance = OrderStore()
    return _store_instance
