"""
Talks to legacy system
=>This file is dumb on purpose:
* no validation
* no safety
* no buisness logic
Because legacy is unsafe by design
"""
import requests

LEGACY_BASE_URL = "http://localhost:7000/legacy"

def fetch_menu():
    """Fetches menu from legacy system"""
    response = requests.get(f"{LEGACY_BASE_URL}/menu")
    response.raise_for_status()
    return response.json()

def fetch_inventory():
    """"""
    response = requests.get(f"{LEGACY_BASE_URL}/inventory")
    response.raise_for_status()
    return response.json()

