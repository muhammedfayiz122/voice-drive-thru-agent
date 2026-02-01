import json
from langchain.messages import HumanMessage
from app.agent.state import AgentState
from app.agent.utils.llm import get_llm
from app.agent.prompt.prompt_library import INTENT_PROMPT
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from app.agent.schema.schemas import IntentAnalysisResult

from dotenv import load_dotenv

load_dotenv()

def llm_intent_analyzer(state: AgentState) -> AgentState:
    # prompt = INTENT_PROMPT.format(input=state["user_input"])
    user_input = state.get("user_input", "")
    
    output_parser = JsonOutputParser(pydantic_object=IntentAnalysisResult)
    llm = get_llm()
    prompt = PromptTemplate(
        template=INTENT_PROMPT, 
        partial_variables={"format_instructions": output_parser.get_format_instructions()},
        input_variables=["input"],
    )
    
    
    try:
        chain = {"input": lambda x: x} | prompt | llm | output_parser
        data = chain.invoke({"input": user_input[:500]})  # Truncate input to first 500 chars
        print(data)
    except Exception as error:
        print(f"Error during LLM intent analysis: {error}")
        
        # try:
        #     print("Falling back to LLM structured output call...")
        #     resp = llm.invoke([HumanMessage(content=INTENT_PROMPT.format(input=user_input[:500]))], IntentAnalysisResult)
        #     data = json.loads(resp.content)
        # except Exception as fallback_error:
        #     print(f"Fallback also failed: {fallback_error}")
        
        state["intent"] = "INVALID"
        state["confidence"] = 0.0
        state["parsed_items"] = []
        state["inventory_target"] = None
        state["error"] = "LLM intent analysis failed"
        return state

    state["intent"] = data.get("intent", "INVALID")
    state["confidence"] = data.get("confidence", None)
    state["parsed_items"] = data.get("order_items", [])
    state["inventory_target"] = data.get("inventory_item", None)

    return state

if __name__ == "__main__":
    # Simple manual test inputs
    test_inputs = [
        "Hi",
        "Order me 2 vanilla ice creams",
        "Is the ice cream machine broken?",
        "Order me 2 ice",
        "What is the weather today?"
    ]

    for text in test_inputs:
        print("=" * 60)
        print(f"USER INPUT: {text}")

        # Minimal initial agent state
        state = {
            "user_input": text,
            "intent": None,
            "confidence": None,
            "parsed_items": [],
            "inventory_target": None,
        }

        # Run intent analyzer
        updated_state = llm_intent_analyzer(state)

        # Pretty-print results
        print("INTENT:", updated_state.get("intent"))
        print("CONFIDENCE:", updated_state.get("confidence"))
        print("PARSED ITEMS:", updated_state.get("parsed_items"))
        print("INVENTORY TARGET:", updated_state.get("inventory_target"))
