from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import (
    llm_intent_analyzer,
    intent_router,
    greeting_response,
    inventory_check,
    confirm_order,
    submit_order_node,
    llm_response,
    invalid_response,
    )

def build_graph():
    g = StateGraph(AgentState)

    g.add_node("intent_analyzer", llm_intent_analyzer)
    g.add_node("greeting_response", greeting_response)
    g.add_node("inventory_check", inventory_check)
    g.add_node("confirm_order", confirm_order)
    g.add_node("submit_order", submit_order_node)
    g.add_node("llm_response", llm_response)
    g.add_node("invalid_response", invalid_response)

    g.set_entry_point("intent_analyzer")

    g.add_conditional_edges(
        "intent_analyzer",
        intent_router,
        {
            "greeting_response": "greeting_response",
            "inventory_check": "inventory_check",
            # "order_processing": "confirm_order",
            "invalid_response": "invalid_response",
        }
    )

    g.add_conditional_edges(
        "inventory_check",
        decision_node,
        {
            "confirm_order": "confirm_order",
            "llm_response": "llm_response",
            "end": END,
        }
    )

    g.add_edge("confirm_order", "submit_order")
    g.add_edge("submit_order", END)
    g.add_edge("greeting_response", END)
    g.add_edge("llm_response", END)
    g.add_edge("invalid_response", END)

    return g.compile()
