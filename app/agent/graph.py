from langgraph.graph import StateGraph, START, END
from app.agent.state import AgentState
from app.agent.nodes import llm_intent_analyzer, intent_router
from app.agent.nodes.greet import greeting_response
from app.agent.nodes.order import (
    inventory_check as order_inventory_check,
    unavailable_response,
    confirm_order,
    submit_order_node,
    reject_order_response,
    decision_router,
    confirm_decision_router,
    invalid_confirmation_response,
)
from app.agent.nodes.query import inventory_response, inventory_check as query_inventory_check
from app.agent.nodes.invalid import invalid_response

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("intent_analyzer", llm_intent_analyzer)
    
    # 1) greeting
    graph.add_node("greeting_response", greeting_response)
    
    # 2) order processing
    graph.add_node("order_inventory_check", order_inventory_check)
    graph.add_node("unavailable_response", unavailable_response)
    graph.add_node("confirm_order", confirm_order)
    graph.add_node("submit_order", submit_order_node)
    graph.add_node("reject_order_response", reject_order_response)
    graph.add_node("invalid_confirmation_response", invalid_confirmation_response)

    # 3) query inventory check
    graph.add_node("query_inventory_check", query_inventory_check)
    graph.add_node("inventory_response", inventory_response)
    
    # 4) invalid response
    graph.add_node("invalid_response", invalid_response)
    
    # Entry point
    graph.add_edge(START, "intent_analyzer")

    graph.add_conditional_edges(
        "intent_analyzer",
        intent_router,
        {
            "greeting_response": "greeting_response",
            "inventory_check": "query_inventory_check",
            "order_processing": "order_inventory_check",
            "invalid_response": "invalid_response",
        }
    )


    
    # 1) Greeting and LLM response lead to end
    graph.add_edge("greeting_response", END)
    
    # 2) Confirm order leads to submit order, then to end
    graph.add_conditional_edges(
        "order_inventory_check",
        decision_router,
        {
            "not_available": "unavailable_response", # LLM to inform user of unavailability
            "available": "confirm_order", # proceed to order confirmation
            "check_failed": END, # no action
        }
    )
    # item not available, end via LLM response
    graph.add_edge("unavailable_response", END)
    # item available, proceed to order confirmation
    # graph.add_edge("confirm_order", "submit_order")
    graph.add_conditional_edges(
        "confirm_order",
        confirm_decision_router,
        {
            "confirm": "submit_order",
            "cancel": "reject_order_response", # LLM to inform user of cancellation
            "invalid": "invalid_confirmation_response", # LLM to inform user of invalid response
        }
    )
    graph.add_edge("submit_order", END)

    # 3) Inventory check can lead to end via LLM response
    graph.add_edge("query_inventory_check", "inventory_response")
    graph.add_edge("inventory_response", END)
    
    # 4) LLM response and invalid response lead to end
    graph.add_edge("invalid_response", END)
    graph.add_edge("invalid_confirmation_response", END)

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
    import time
    agent_graph = build_graph()
    _generate_graph_image(agent_graph)
    start_time = time.perf_counter()
    result = agent_graph.invoke({
        "user_input": "Hello, I want Grilled Chicken Panini"
    })
    elapsed = time.perf_counter() - start_time
    print("Final State:", result)
    print(f"Execution Time: {elapsed:.3f} seconds")
