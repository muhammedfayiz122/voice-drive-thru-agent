"""
Safety rules
this is the file where validation happens
Becasue we dont trust AI blindly
"""

def validate_item_exists(item_code: str, menu_items: dict) -> bool:
    """
    Validates if an item exists in the menu
    Args:
        item_code (str): item code provided by AI.
        menu_items (dict): menu provided by legacy system.
    """
    for item in menu_items:
        if item["item_code"] == item_code:
            return True
    return False

def validate_quantity(quantity: int) -> bool:
    """
    Validates if the quantity is a positive integer
    Args:
        quantity (int): quantity provided by AI.
    """
    return 0 <= quantity <= 10

def check_inventory(item_code: str, inventory: dict) -> bool:
    stock = inventory.get("stock_levels", {}).get(item_code, 0)
    machine_status = inventory.get("machines", {}) \
                          .get("ICE_CREAM_MACHINE", {}) \
                          .get("status", "WORKING")

    if item_code.startswith("ICE") and machine_status != "WORKING":
        return False, "Ice cream machine is broken"

    if stock <= 0:
        return False, "Item out of stock"

    return True, "Available"