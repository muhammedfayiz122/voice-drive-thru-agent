from app.agent.state import AgentState

def intent_router(state: AgentState) -> str:
    if state["intent"] == "GREETING":
        return "greeting_response"
    if state["intent"] == "ORDER":
        return "order_processing"
    if state["intent"] == "INVENTORY_QUESTION":
        return "inventory_check"
    return "invalid_response"