"""

# CRTICAL: Should integrate LLM for more natural speech.

thsi node handles SHOW_MENU intent.

# NOTE: Uses MenuCache for instant response.
# NOTE: No MCP calls in request path.

1. Gives brief category overview (NOT full menu)
2. Asks what type of food customer wants
"""

from app.agent.state import AgentState
from app.agent.utils.menu_cache import MenuCache

class ShowMenuNode:
    def __init__(self):
        pass
    
    def __call__(self, state: AgentState) -> dict:
        """
        Handles customer asking to see the menu.
        # NOTE: Uses cached menu 
        # NOTE: No MCP calls in request path.
        
        1. Gets categories from cached menu
        2. Gives BRIEF category overview
        3. Asks what type they're interested in
        
        Note: never list all items - voice inefficient.
        
        Args:
            state: current agent state
        Returns:
            dict: updated state with response_text
        """
        try:
            # Use cached categories - NO MCP CALL!
            categories = MenuCache.get_categories()
            if not categories:
                # CRITICAL: Fallback response , should solve
                return { 
                    "response_text": "We've got pizza, pasta, salads, sandwiches, "
                                    "soups, and desserts. What sounds good?",
                    "conversation_complete": False
                }
            
            response = self._format_brief_overview(categories)    
            return {
                "response_text": response,
                "conversation_complete": False
            }
            
        except Exception as e:
            return {
                "response_text": "We've got Italian food - pizza, pasta, salads, "
                                "and desserts. What are you in the mood for?",
                "conversation_complete": False
            }


    def _get_categories(self, menu: list) -> list:
        """
        Extracts unique categories from menu.
        
        1. Iterates menu items
        2. Collects unique category names
        
        Args:
            menu: Menu items from MCP
        
        Returns:
            list: Unique category names
        """
        categories = []
        for item in menu:
            cat = item.get("category", "Other")
            if cat not in categories:
                categories.append(cat)
        return categories


    def _format_brief_overview(self, categories: list) -> str:
        """
        Formats brief category overview for voice.
        1. lists categories naturally
        2. asks what type interests them
        3. keeps low latency
        
        Note: Don't list items - just categories.
        
        Args:
            categories: list of category names
        Returns:
            str: brief voice-friendly response
        """
        if len(categories) == 0:
            return "We are currently updating our menu. What are you in the mood for?"
        
        if len(categories) == 1:
            return f"We've got {categories[0].lower()}. What would you like?"
        
        if len(categories) == 2:
            category_overview_text = f"{categories[0].lower()} and {categories[1].lower()}"
        else:
            # Natural list: "pizza, pasta, salads, and desserts"
            category_overview_text = ", ".join(c.lower() for c in categories[:-1])
            category_overview_text += f", and {categories[-1].lower()}"
        
        return f"We've got {category_overview_text}. What sounds good to you?"

show_menu_node = ShowMenuNode()