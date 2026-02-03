"""
Intent analyzer node - Classifies customer speech using LLM.
1. Receives user_input from state
2. Formats cart and history as context
3. Calls LLM to classify intent
4. Extracts items, modifications, query targets
"""

from app.agent.state import AgentState
from app.agent.utils.llm import get_llm
from app.agent.prompt.prompt_library import PROMPT_REGISTRY
from app.agent.schema.schemas import IntentAnalysisResult
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from app.utils.logger import get_logger

logger = get_logger(__name__)

class IntentAnalyzer:
    def __init__(self):
        self.intent_prompt = PROMPT_REGISTRY["intent_prompt"]
        
    def format_cart_state(self, cart_items: list) -> str:
        """
        Formats cart items for prompt context.
        1. Returns "Cart is empty" if no items
        2. Formats each item as "- quantity x name ($total)"
        
        Args:
            cart_items: list of CartItem dicts
        Returns:
            str: formatted cart string for prompt
        """
        if not cart_items:
            return "Cart is empty"
        
        lines = []
        for item in cart_items:
            lines.append(f"- {item['quantity']}x {item['menu_name']} (${item['item_total']})")
        return "\n".join(lines)


    def format_conversation_history(self, history: list) -> str:
        """
        Formats conversation history for prompt context.
        1. Returns "No previous conversation" if empty
        2. Formats last 6 turns as "Role: content"
        
        # NOTE: Limits to 6 turns to avoid token overflow.
        
        Args:
            history: list of {"role": "user/agent", "content": "..."}
        Returns:
            str: formatted history string for prompt
        """
        if not history:
            return "No previous conversation"
        
        lines = []
        for turn in history[-6:]:
            role = "Customer" if turn["role"] == "user" else "Agent"
            lines.append(f"{role}: {turn['content']}")
        return "\n".join(lines)


    def __call__(self, state: AgentState) -> AgentState:
        """
        Analyzes customer intent using LLM.
        1. Builds prompt with cart context and history
        2. Calls LLM with JsonOutputParser
        3. Extracts intent, confidence, items using LLM
        
        4. Handles MODIFY/REMOVE targets
        5. Handles INVENTORY_QUESTION query_item
        
        Args:
            state: current agent state with user_input
        Returns:
            dict: updated state with intent, confidence, parsed_items
        """
        logger.info("Analyzing customer intent...")
        
        user_input = state.get("user_input", "")
        cart_items = state.get("cart_items", [])
        history = state.get("conversation_history", [])
        
        # Output parser
        output_parser = JsonOutputParser(pydantic_object=IntentAnalysisResult)
        
        # LLM
        llm = get_llm()

        # Prompt
        prompt = PromptTemplate(
            template=self.intent_prompt,
            input_variables=["user_input", "cart_state", "conversation_history"],
            partial_variables={"format_instructions": output_parser.get_format_instructions()},
        )
        
        try:
            # LCEL chain
            chain = prompt | llm | output_parser
            data = chain.invoke({
                "user_input": user_input,
                "cart_state": self.format_cart_state(cart_items),
                "conversation_history": self.format_conversation_history(history),
            })
            
            logger.info(f"Intent: {data.get('intent')} (confidence: {data.get('confidence')})")
            
            state["intent"] = data.get("intent", "UNCLEAR")
            state["confidence"] = data.get("confidence", 0.0)
            state["parsed_items"] = data.get("items", [])
            
            # Handle modifications (for MODIFY/REMOVE)
            target_item = data.get("target_item")
            new_quantity = data.get("new_quantity")
            if target_item:
                state["modifications"] = {
                    "modification_target": target_item,
                    "item_name": target_item,
                    "new_quantity": new_quantity if new_quantity is not None else 0
                }
            else:
                state["modifications"] = None
            
            # Handle inventory question (query_item)
            query_item = data.get("query_item")
            if query_item and not state["parsed_items"]:
                state["parsed_items"] = [{"name": query_item, "quantity": 1}]
            
        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            state["intent"] = "UNCLEAR"
            state["confidence"] = 0.0
            state["parsed_items"] = []
            state["error"] = str(e)
        
        return state

intent_analyzer = IntentAnalyzer()