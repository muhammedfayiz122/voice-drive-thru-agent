"""
KDS Main - Combined launcher for KDS display and API.

Usage:
    python -m app.kds.main

Starts:
    1. PyQt6 KDS Display window
    2. FastAPI server on port 8001 for receiving orders
"""

import sys
import threading
import uvicorn
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from app.kds.display import KDSMainWindow
from app.kds.order_store import get_order_store


def run_api_server():
    """Run FastAPI server in background thread."""
    from app.kds.api import app
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="warning")


def main():
    """Main entry point - runs KDS display with API server."""
    
    # Initialize Qt application
    qt_app = QApplication(sys.argv)
    qt_app.setStyle("Fusion")
    
    # Initialize store before starting threads
    store = get_order_store()
    
    # Start API server in background thread
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    print("KDS API running on http://127.0.0.1:8002")
    
    # Create and show main window
    window = KDSMainWindow()
    window.show()
    print("🖥️  KDS Display started")
    print("\nSubmit orders via POST http://127.0.0.1:8002/kds/order")
    print("   Example: curl -X POST http://127.0.0.1:8002/kds/order -H 'Content-Type: application/json' -d '{\"items\": [{\"item_code\": \"PZ001\", \"name\": \"Margherita Pizza\", \"quantity\": 2, \"price\": 199}]}'")
    
    # Run Qt event loop
    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()
