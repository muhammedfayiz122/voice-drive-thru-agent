"""
Safety rules and validation logic.
This is where validation happens because we don't trust AI blindly.
"""

from difflib import SequenceMatcher


def validate_item_exists(item_code: str, menu_items: list) -> bool:
    """
    Validates if an item exists in the menu by item_code.
    
    Args:
        item_code: Item code provided by AI
        menu_items: Menu list from legacy system
    
    Returns:
        bool: True if item exists, False otherwise
    """
    for item in menu_items:
        if item["item_code"] == item_code:
            return True
    return False


def validate_quantity(quantity: int) -> bool:
    """
    Validates if quantity is within acceptable range.
    
    1. Checks quantity is between 0 and 10 (inclusive)
    
    Note: Max 10 items per order to prevent abuse.
    
    Args:
        quantity: Quantity provided by AI
    
    Returns:
        bool: True if valid, False otherwise
    """
    return 0 <= quantity <= 10


def check_inventory(item_code: str, inventory: dict) -> tuple[bool, str]:
    """
    Checks if item is available in inventory.
    
    1. Checks stock level for item_code
    2. For ICE* items, checks ice cream machine status
    3. Returns availability with reason
    
    Args:
        item_code: Item code to check
        inventory: Inventory data from legacy system
    
    Returns:
        tuple: (is_available, reason_string)
    """
    stock = inventory.get("stock_levels", {}).get(item_code, 0)
    machine_status = inventory.get("machines", {}) \
                          .get("ICE_CREAM_MACHINE", {}) \
                          .get("status", "WORKING")

    if item_code.startswith("ICE") and machine_status != "WORKING":
        return False, "Ice cream machine is currently down"

    if stock <= 0:
        return False, "Out of stock"

    return True, "Available"


def _calculate_similarity(s1: str, s2: str) -> float:
    """
    Calculates similarity ratio between two strings.
    1. Uses SequenceMatcher for fuzzy comparison
    2. Returns ratio between 0.0 and 1.0
    
    Args:
        s1: first string
        s2: second string
    Returns:
        float: similarity ratio (0.0 to 1.0)
    """
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def _tokenize(text: str) -> set:
    """
    Tokenizes text into lowercase words.
    
    1. Splits by whitespace
    2. Converts to lowercase set
    
    Args:
        text: Input text
    
    Returns:
        set: Set of lowercase tokens
    """
    return set(text.lower().split())


def match_menu_item(item_name: str, menu_items: list) -> dict | None:
    """
    Matches user's spoken item name to actual menu item.
    
    1. Exact match (case-insensitive)
    2. Substring match (item_name in menu_name or vice versa)
    3. Token overlap match (shared words between names)
    4. Fuzzy match using similarity ratio (threshold: 0.6)
    
    Note: Returns first best match. For voice agents, fuzzy matching
    is critical due to transcription errors.
    
    Args:
        item_name: Item name spoken by customer
        menu_items: Menu list from legacy system
    
    Returns:
        dict: Matched menu item or None if no match
    """
    item_name_lower = item_name.lower().strip()
    
    # 1) Exact match
    for item in menu_items:
        if item["name"].lower() == item_name_lower:
            return item
    
    # 2) Substring match
    for item in menu_items:
        menu_name_lower = item["name"].lower()
        if item_name_lower in menu_name_lower or menu_name_lower in item_name_lower:
            return item
    
    # 3) Token overlap match
    input_tokens = _tokenize(item_name)
    best_token_match = None
    best_token_overlap = 0
    
    for item in menu_items:
        menu_tokens = _tokenize(item["name"])
        overlap = len(input_tokens & menu_tokens)
        if overlap > best_token_overlap:
            best_token_overlap = overlap
            best_token_match = item
    
    if best_token_overlap >= 1:
        return best_token_match
    
    # 4) Fuzzy match (Levenshtein-like)
    best_fuzzy_match = None
    best_fuzzy_score = 0.0
    FUZZY_THRESHOLD = 0.6
    
    for item in menu_items:
        score = _calculate_similarity(item_name, item["name"])
        if score > best_fuzzy_score:
            best_fuzzy_score = score
            best_fuzzy_match = item
    
    if best_fuzzy_score >= FUZZY_THRESHOLD:
        return best_fuzzy_match
    
    return None


def get_similar_items(item_name: str, menu_items: list, top_n: int = 3) -> list:
    """
    Returns similar menu items for suggestions.
    
    1. Calculates similarity for all menu items
    2. Sorts by similarity score descending
    3. Returns top N items above threshold
    
    Note: Used for "did you mean..." suggestions.
    
    Args:
        item_name: Item name spoken by customer
        menu_items: Menu list from legacy system
        top_n: Number of suggestions to return
    
    Returns:
        list: Top N similar menu items with scores
    """
    SUGGESTION_THRESHOLD = 0.3
    
    scored_items = []
    for item in menu_items:
        score = _calculate_similarity(item_name, item["name"])
        if score >= SUGGESTION_THRESHOLD:
            scored_items.append({"item": item, "score": score})
    
    scored_items.sort(key=lambda x: x["score"], reverse=True)
    return [s["item"] for s in scored_items[:top_n]]