from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes import llm_intent_analyzer, intent_router
from app.agent.nodes.greet import greeting_response
from app.agent.nodes.order import ()
from app.agent.nodes.order import decision_router
from app.agent.nodes import intent_router

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("intent_analyzer", llm_intent_analyzer)
    
    # 1) greeting
    graph.add_node("greeting_response", greeting_response)
    
    # 2) order processing
    graph.add_node("order_inventory_check", inventory_check)
    graph.add_node("llm_response", llm_response)
    graph.add_node("confirm_order", confirm_order)
    graph.add_node("submit_order", submit_order_node)
    graph.add_node("query_inventory_response", inventory_response) # TODO
    graph.add_node("order_inventory_response", inventory_response) # TODO
    graph.add_node("invalid_response", invalid_response)

    graph.set_entry_point("intent_analyzer")

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
            "not_available": "llm_response", # LLM to inform user of unavailability
            "available": "confirm_order", # proceed to order confirmation
            "end": END, # no action
        }
    )
    # item not available, end via LLM response
    graph.add_edge("llm_response", END)
    # item available, proceed to order confirmation
    # graph.add_edge("confirm_order", "submit_order")
    graph.add_conditional_edges(
        "confirm_order",
        confirm_decision_router,
        {
            "confirm": "submit_order",
            "cancel": "reject_order_response", # LLM to inform user of cancellation
            "invalid": "llm_response", # LLM to inform user of invalid response
        }
    )
    graph.add_edge("submit_order", END)

    # 3) Inventory check can lead to end via LLM response
    graph.add_edge("inventory_check", "inventory_response")
    graph.add_edge("inventory_response", END)
    
    # 4) LLM response and invalid response lead to end
    graph.add_edge("llm_response", END)
    graph.add_edge("invalid_response", END)

    return graph.compile()
