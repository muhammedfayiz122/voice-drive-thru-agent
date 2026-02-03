"""
Talks to legacy system
=>This file is dumb on purpose:
* no validation
* no safety
* no buisness logic
Because legacy is unsafe by design
"""
import requests
from app.config import settings


LEGACY_BASE_URL = f"{settings.legacy_system_url}/legacy"

def fetch_menu():
    """Fetches menu from legacy system"""
    response = requests.get(f"{LEGACY_BASE_URL}/menu")
    response.raise_for_status()
    return response.json()

def fetch_inventory():
    """Fetches full inventory from legacy system"""
    response = requests.get(f"{LEGACY_BASE_URL}/inventory")
    response.raise_for_status()
    return response.json()

