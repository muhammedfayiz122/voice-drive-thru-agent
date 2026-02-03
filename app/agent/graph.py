"""
LangGraph Definition - Defines the conversation flow graph.

1. Registers all handler nodes
2. Connects intent analyzer to router
3. Routes to appropriate handler based on intent
4. All handlers return to END (single-turn design)

Note: State managed externally in main loop.
"""

from langgraph.graph import StateGraph, START, END
from app.agent.state import AgentState

from app.agent.nodes import (
    intent_analyzer,
    intent_router,
    greeting_node,
    order_handler,
    modify_handler,
    remove_handler,
    done_ordering_node,
    cancel_order_node,
    inventory_query_node,
    repeat_order_node,
    unclear_handler,
    show_menu_node,
)


def build_graph():
    """
    Builds and compiles the LangGraph state machine.
    
    1. Creates StateGraph with AgentState schema
    2. Adds all handler nodes
    3. Configures conditional routing from intent analyzer
    4. Connects all handlers to END
    
    Returns:
        CompiledGraph: Ready-to-invoke graph
    """
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
    graph.add_node("show_menu", show_menu_node)
    
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
            "show_menu": "show_menu",
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
    graph.add_edge("show_menu", END)
    
    return graph.compile()

def _generate_graph_image(graph, output_file_path: str = "workflow/agent_graph.png") -> bool:
    """Generate and save the LangGraph image."""
    from langchain_core.runnables.graph_mermaid import draw_mermaid_png
    from pathlib import Path
    import os
    if not os.path.exists(os.path.dirname(output_file_path)):
        Path(os.path.dirname(output_file_path)).mkdir(parents=True, exist_ok=True)
    mermaid_syntax = graph.get_graph().draw_mermaid()
    draw_mermaid_png(mermaid_syntax, output_file_path=output_file_path)
    return True

if __name__ == "__main__":
    graph = build_graph()
    _generate_graph_image(graph)
    print("LangGraph compiled successfully.")