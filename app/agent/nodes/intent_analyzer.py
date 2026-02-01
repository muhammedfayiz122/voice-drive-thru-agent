from app.agent.state import AgentState
from app.agent.utils.llm import get_llm
from app.agent.prompt.prompt_library import INTENT_PROMPT
from app.agent.schema.schemas import IntentAnalysisResult
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from app.utils.logger import get_logger

logger = get_logger(__name__)

def format_cart_state(cart_items: list) -> str:
    """Format cart items for prompt context."""
    if not cart_items:
        return "Cart is empty"
    
    lines = []
    for item in cart_items:
        lines.append(f"- {item['quantity']}x {item['menu_name']} (₹{item['item_total']})")
    return "\n".join(lines)

def format_conversation_history(history: list) -> str:
    """Format conversation history for prompt context."""
    if not history:
        return "No previous conversation"
    
    lines = []
    for turn in history[-6:]:  # Last 6 turns for context
        role = "Customer" if turn["role"] == "user" else "Agent"
        lines.append(f"{role}: {turn['content']}")
    return "\n".join(lines)

def intent_analyzer(state: AgentState) -> AgentState:
    """
    Analyzes customer intent using LLM.
    Extracts intent, items, and modification targets.
    """
    logger.info("Analyzing customer intent...")
    
    user_input = state.get("user_input", "")
    cart_items = state.get("cart_items", [])
    history = state.get("conversation_history", [])
    
    output_parser = JsonOutputParser(pydantic_object=IntentAnalysisResult)
    llm = get_llm()
    
    prompt = PromptTemplate(
        template=INTENT_PROMPT,
        input_variables=["user_input", "cart_state", "conversation_history"],
        partial_variables={"format_instructions": output_parser.get_format_instructions()},
    )
    
    try:
        chain = prompt | llm | output_parser
        data = chain.invoke({
            "user_input": user_input,
            "cart_state": format_cart_state(cart_items),
            "conversation_history": format_conversation_history(history),
        })
        
        logger.info(f"Intent: {data.get('intent')} (confidence: {data.get('confidence')})")
        
        state["intent"] = data.get("intent", "UNCLEAR")
        state["confidence"] = data.get("confidence", 0.0)
        state["parsed_items"] = data.get("items", [])
        
        # Handle modifications
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
        
    except Exception as e:
        logger.error(f"Intent analysis failed: {e}")
        state["intent"] = "UNCLEAR"
        state["confidence"] = 0.0
        state["parsed_items"] = []
        state["error"] = str(e)
    
    return state
