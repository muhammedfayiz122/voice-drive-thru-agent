from app.agent.state import AgentState


def invalid_confirmation_response(state: AgentState) -> AgentState:
    state["response_text"] = (
        "I'm sorry, I didn't understand your confirmation. "
    )
    return state
