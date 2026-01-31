from app.agent.state import AgentState

def decision_router(state: AgentState) -> str:
    if state["inventory_available"]:
        return "confirm_order"
    if state["inventory_unavailable"]:
        return "llm_response"
    return "end"