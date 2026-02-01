from app.agent.state import AgentState

def decision_router(state: AgentState) -> str:
    if state["all_items_available"]:
        return "available"
    if not state["all_items_available"]:
        return "not_available"
    return "check_failed"