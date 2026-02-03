"""
KDS Display - PyQt6 Kitchen Display System GUI.

1. Shows pending orders in card layout
2. Auto-refreshes when new orders arrive
3. Allows marking orders as complete
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QFrame, QGridLayout, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QColor, QPalette

from app.kds.models import Order, OrderStatus
from app.kds.order_store import get_order_store


# Modern color palette
COLORS = {
    "primary": "#6366F1",       # Indigo
    "primary_dark": "#4F46E5",
    "success": "#10B981",       # Emerald
    "success_dark": "#059669",
    "warning": "#F59E0B",       # Amber
    "warning_dark": "#D97706",
    "danger": "#EF4444",        # Red
    "background": "#F8FAFC",    # Slate-50
    "surface": "#FFFFFF",
    "text_primary": "#1E293B",  # Slate-800
    "text_secondary": "#64748B", # Slate-500
    "border": "#E2E8F0",        # Slate-200
    "pending_bg": "#FEF3C7",    # Amber-100
    "pending_border": "#FCD34D", # Amber-300
    "progress_bg": "#DBEAFE",   # Blue-100
    "progress_border": "#60A5FA", # Blue-400
}


class OrderCard(QFrame):
    """
    Single order display card with modern styling.
    
    Shows order ID, items, total, and action buttons.
    """
    
    def __init__(self, order: Order, parent=None):
        super().__init__(parent)
        self.order = order
        self.setup_ui()
        
    def setup_ui(self):
        self.setMinimumWidth(300)
        self.setMaximumWidth(340)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        
        # Set background color based on status
        self._update_style()
        
        # Add drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header with status badge
        header_layout = QHBoxLayout()
        
        # Order ID
        order_id_short = self.order.order_id.split("-")[-1] if "-" in self.order.order_id else self.order.order_id
        header = QLabel(f"#{order_id_short}")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        # Status badge
        status_badge = QLabel(self.order.status.value.upper())
        status_badge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        if self.order.status == OrderStatus.PENDING:
            badge_style = f"background-color: {COLORS['warning']}; color: white;"
        else:
            badge_style = f"background-color: {COLORS['primary']}; color: white;"
        status_badge.setStyleSheet(f"""
            {badge_style}
            padding: 4px 10px;
            border-radius: 10px;
        """)
        header_layout.addWidget(status_badge)
        
        layout.addLayout(header_layout)
        
        # Time with icon
        time_label = QLabel(f"🕐  {self.order.created_at.strftime('%H:%M:%S')}")
        time_label.setFont(QFont("Segoe UI", 11))
        time_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        layout.addWidget(time_label)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(line)
        
        # Items list
        items_widget = QWidget()
        items_widget.setStyleSheet("background: transparent;")
        items_layout = QVBoxLayout(items_widget)
        items_layout.setContentsMargins(0, 4, 0, 4)
        items_layout.setSpacing(8)
        
        for item in self.order.items:
            item_row = QHBoxLayout()
            
            # Quantity badge
            qty_label = QLabel(f"{item.quantity}×")
            qty_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            qty_label.setStyleSheet(f"""
                color: {COLORS['primary']};
                background-color: {COLORS['primary']}15;
                padding: 2px 8px;
                border-radius: 4px;
            """)
            qty_label.setFixedWidth(40)
            qty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            name_label = QLabel(item.name)
            name_label.setFont(QFont("Segoe UI", 12))
            name_label.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
            name_label.setWordWrap(True)
            
            price_label = QLabel(f"₹{item.price * item.quantity:.0f}")
            price_label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
            price_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
            price_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            item_row.addWidget(qty_label)
            item_row.addSpacing(8)
            item_row.addWidget(name_label, 1)
            item_row.addWidget(price_label)
            
            items_layout.addLayout(item_row)
        
        layout.addWidget(items_widget)
        
        # Separator
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFixedHeight(1)
        line2.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(line2)
        
        # Total section
        total_layout = QHBoxLayout()
        total_text = QLabel("Total")
        total_text.setFont(QFont("Segoe UI", 13))
        total_text.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        total_value = QLabel(f"₹{self.order.total:.0f}")
        total_value.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        total_value.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        total_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        total_layout.addWidget(total_text)
        total_layout.addWidget(total_value)
        layout.addLayout(total_layout)
        
        layout.addSpacing(4)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        if self.order.status == OrderStatus.PENDING:
            start_btn = QPushButton("▶  Start Preparing")
            start_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            start_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['success']};
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 8px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['success_dark']};
                }}
                QPushButton:pressed {{
                    background-color: #047857;
                }}
            """)
            start_btn.clicked.connect(self._on_start)
            btn_layout.addWidget(start_btn)
            
        elif self.order.status == OrderStatus.IN_PROGRESS:
            done_btn = QPushButton("✓  Mark Complete")
            done_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            done_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            done_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['primary']};
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 8px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['primary_dark']};
                }}
                QPushButton:pressed {{
                    background-color: #4338CA;
                }}
            """)
            done_btn.clicked.connect(self._on_done)
            btn_layout.addWidget(done_btn)
        
        layout.addLayout(btn_layout)
        
    def _update_style(self):
        """Update card style based on status."""
        if self.order.status == OrderStatus.PENDING:
            bg_color = COLORS['pending_bg']
            border_color = COLORS['pending_border']
        elif self.order.status == OrderStatus.IN_PROGRESS:
            bg_color = COLORS['progress_bg']
            border_color = COLORS['progress_border']
        else:
            bg_color = COLORS['surface']
            border_color = COLORS['border']
            
        self.setStyleSheet(f"""
            OrderCard {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 12px;
            }}
        """)
    
    def _on_start(self):
        """Mark order as in progress."""
        store = get_order_store()
        store.update_status(self.order.order_id, OrderStatus.IN_PROGRESS)
        
    def _on_done(self):
        """Mark order as completed."""
        store = get_order_store()
        store.update_status(self.order.order_id, OrderStatus.COMPLETED)


class KDSMainWindow(QMainWindow):
    """
    Main KDS window with modern order grid display.
    """
    
    def __init__(self):
        super().__init__()
        self.store = get_order_store()
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        self.setWindowTitle("Kitchen Display System")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet(f"background-color: {COLORS['background']};")
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header with gradient feel
        header = QWidget()
        header.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['primary']}, stop:1 {COLORS['primary_dark']});
        """)
        header.setFixedHeight(70)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        
        # Logo and title
        title_layout = QHBoxLayout()
        title_layout.setSpacing(12)
        
        logo = QLabel("🍔")
        logo.setFont(QFont("Segoe UI Emoji", 28))
        logo.setStyleSheet("background: transparent;")
        title_layout.addWidget(logo)
        
        title = QLabel("Kitchen Display System")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        title_layout.addWidget(title)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Clear completed button
        clear_btn = QPushButton("🗑  Clear Completed")
        clear_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.15);
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.3);
                padding: 10px 20px;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.25);
                border-color: rgba(255, 255, 255, 0.5);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
        """)
        clear_btn.clicked.connect(self._clear_completed)
        header_layout.addWidget(clear_btn)
        
        main_layout.addWidget(header)
        
        # Stats bar
        stats_bar = QWidget()
        stats_bar.setStyleSheet(f"background-color: {COLORS['surface']}; border-bottom: 1px solid {COLORS['border']};")
        stats_bar.setFixedHeight(50)
        stats_layout = QHBoxLayout(stats_bar)
        stats_layout.setContentsMargins(24, 0, 24, 0)
        
        self.stats_label = QLabel("Orders: 0 pending | 0 in progress")
        self.stats_label.setFont(QFont("Segoe UI", 13))
        self.stats_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        stats_layout.addWidget(self.stats_label)
        
        stats_layout.addStretch()
        
        # Live indicator
        live_indicator = QLabel("● LIVE")
        live_indicator.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        live_indicator.setStyleSheet(f"color: {COLORS['success']}; background: transparent;")
        stats_layout.addWidget(live_indicator)
        
        main_layout.addWidget(stats_bar)
        
        # Scroll area for orders
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {COLORS['background']};
            }}
            QScrollBar:vertical {{
                background-color: {COLORS['background']};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLORS['border']};
                border-radius: 6px;
                min-height: 40px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLORS['text_secondary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        
        self.orders_container = QWidget()
        self.orders_container.setStyleSheet(f"background-color: {COLORS['background']};")
        self.orders_layout = QGridLayout(self.orders_container)
        self.orders_layout.setSpacing(20)
        self.orders_layout.setContentsMargins(24, 24, 24, 24)
        self.orders_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        scroll.setWidget(self.orders_container)
        main_layout.addWidget(scroll, 1)
        
        # Initial refresh
        self.refresh_orders()
        
    def connect_signals(self):
        """Connect store signals to UI updates."""
        self.store.order_added.connect(self._on_order_added)
        self.store.order_updated.connect(self._on_order_updated)
        
    @pyqtSlot(str)
    def _on_order_added(self, order_id: str):
        """Handle new order."""
        self.refresh_orders()
        
    @pyqtSlot(str)
    def _on_order_updated(self, order_id: str):
        """Handle order update."""
        self.refresh_orders()
        
    def refresh_orders(self):
        """Rebuild order grid from store."""
        # Clear existing widgets
        while self.orders_layout.count():
            item = self.orders_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get active orders (not completed)
        orders = [o for o in self.store.get_all_orders() 
                  if o.status != OrderStatus.COMPLETED]
        
        # Sort: IN_PROGRESS first, then PENDING, by time
        orders.sort(key=lambda o: (
            0 if o.status == OrderStatus.IN_PROGRESS else 1,
            o.created_at
        ))
        
        # Add order cards in grid (3 columns)
        cols = 3
        for i, order in enumerate(orders):
            row = i // cols
            col = i % cols
            card = OrderCard(order)
            self.orders_layout.addWidget(card, row, col)
        
        # Update stats with better formatting
        pending = len([o for o in orders if o.status == OrderStatus.PENDING])
        in_progress = len([o for o in orders if o.status == OrderStatus.IN_PROGRESS])
        self.stats_label.setText(f"📋 {pending} pending  •  🔥 {in_progress} in progress")
        
    def _clear_completed(self):
        """Clear completed orders."""
        self.store.clear_completed()
        self.refresh_orders()


def run_kds():
    """Launch KDS application."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Set palette for better rendering
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(COLORS['background']))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(COLORS['text_primary']))
    app.setPalette(palette)
    
    window = KDSMainWindow()
    window.show()
    
    return app, window


if __name__ == "__main__":
    app, window = run_kds()
    sys.exit(app.exec())
