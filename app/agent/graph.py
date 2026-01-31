from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes import (
    parse_input,
    check_inventory as check_inventory_node,
    decide_next as decide_next_step,
    confirm_order,
    submit_order as submit_order_node,
)

def build_agent_graph():
    graph = StateGraph(AgentState)

    graph.add_node("parse_input", parse_input)
    graph.add_node("check_inventory", check_inventory_node)
    graph.add_node("confirm_order", confirm_order)
    graph.add_node("submit_order", submit_order_node)

    graph.set_entry_point("parse_input")

    graph.add_edge("parse_input", "check_inventory")

    graph.add_conditional_edges(
        "check_inventory",
        decide_next_step,
        {
            "confirm_order": "confirm_order",
            "end": END,
        },
    )

    graph.add_edge("confirm_order", "submit_order")
    graph.add_edge("submit_order", END)

    return graph.compile()
