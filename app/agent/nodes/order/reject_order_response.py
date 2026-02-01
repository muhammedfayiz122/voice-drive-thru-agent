from app.agent.state import AgentState


def reject_order_response(state: AgentState) -> AgentState:
    state["response_text"] = (
        "I'm sorry, but we are unable to fulfill your order at this time. "
    )
    state["expects_user_reply"] = False
    return state
