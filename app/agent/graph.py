from langgraph.graph import StateGraph, START, END
from app.agent.state import AgentState

from app.agent.nodes.intent_analyzer import intent_analyzer
from app.agent.nodes.intent_router import intent_router
from app.agent.nodes.greeting import greeting_node
from app.agent.nodes.order_handler import order_handler
from app.agent.nodes.modify_handler import modify_handler
from app.agent.nodes.remove_handler import remove_handler
from app.agent.nodes.done_ordering import done_ordering_node
from app.agent.nodes.cancel_order import cancel_order_node
from app.agent.nodes.inventory_query import inventory_query_node
from app.agent.nodes.repeat_order import repeat_order_node
from app.agent.nodes.unclear_handler import unclear_handler

def build_graph():
    graph = StateGraph(AgentState)
    
    # Nodes
    graph.add_node("intent_analyzer", intent_analyzer)
    graph.add_node("greeting", greeting_node)
    graph.add_node("order_handler", order_handler)          # Handles ORDER and ADD_MORE
    graph.add_node("modify_handler", modify_handler)
    graph.add_node("remove_handler", remove_handler)
    graph.add_node("done_ordering", done_ordering_node)
    graph.add_node("cancel_order", cancel_order_node)
    graph.add_node("inventory_query", inventory_query_node)
    graph.add_node("repeat_order", repeat_order_node)
    graph.add_node("unclear_handler", unclear_handler)
    
    # Entry
    graph.add_edge(START, "intent_analyzer")
    
    # Intent routing
    graph.add_conditional_edges(
        "intent_analyzer",
        intent_router,
        {
            "greeting": "greeting",
            "order": "order_handler",
            "modify": "modify_handler",
            "remove": "remove_handler",
            "done": "done_ordering",
            "cancel": "cancel_order",
            "inventory": "inventory_query",
            "repeat": "repeat_order",
            "unclear": "unclear_handler",
        }
    )
    
    # All nodes go to END (single-turn, state managed externally)
    graph.add_edge("greeting", END)
    graph.add_edge("order_handler", END)
    graph.add_edge("modify_handler", END)
    graph.add_edge("remove_handler", END)
    graph.add_edge("done_ordering", END)
    graph.add_edge("cancel_order", END)
    graph.add_edge("inventory_query", END)
    graph.add_edge("repeat_order", END)
    graph.add_edge("unclear_handler", END)
    
    return graph.compile()