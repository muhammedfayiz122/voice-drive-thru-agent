"""
Voice Drive-Thru Agent - Main Conversation Loop.

1. Initializes MenuCache at startup (CRITICAL for latency)
2. Builds LangGraph agent
3. Manages cart state externally
4. Handles conversation loop
5. Updates history after each turn

Note: In production, user_input from STT, response to TTS.
"""

import time

from app.agent.graph import build_graph
from app.agent.utils.menu_cache import MenuCache
from app.utils.logger import get_logger

logger = get_logger(__name__)


def run_voice_agent():
    """
    Main conversation loop for voice drive-thru agent.
    1. Initializes cache at startup (NO MCP calls in request path)
    2. Initializes graph and state
    3. Takes user input (console or STT)
    4. Invokes graph with current state
    5. Updates cart and history from result
    6. Outputs response (print or TTS)
    7. Resets on order completion
    
    Note: State managed externally, passed fresh each invoke.
    """
    # Initialize cache ONCE at startup - critical for latency!
    logger.info("Initializing MenuCache...")
    cache_start = time.perf_counter()
    MenuCache.initialize()
    cache_time = (time.perf_counter() - cache_start) * 1000
    logger.info(f"MenuCache initialized in {cache_time:.0f}ms")
    
    agent = build_graph()
    
    # Conversation state (persists across turns)
    cart_items = []
    cart_total = 0.0
    conversation_history = []
    
    print("=" * 50)
    print("  Drive-Thru Agent Ready")
    print("  Type 'quit' to exit")
    print("=" * 50)
    print()
    
    while True:
        # Get input (voice transcription in production)
        try:
            user_input = input("Customer: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if not user_input:
            continue
            
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        
        # Invoke agent with current state
        try:
            start_time = time.perf_counter()
            result = agent.invoke({
                "user_input": user_input,
                "cart_items": cart_items,
                "cart_total": cart_total,
                "conversation_history": conversation_history,
            })
            latency = (time.perf_counter() - start_time) * 1000  # Convert to ms
        except Exception as e:
            logger.error(f"Agent invocation failed: {e}")
            print(f"Agent: Sorry, something went wrong. Please try again.\n")
            continue
        
        # Update state from result
        cart_items = result.get("cart_items", cart_items)
        cart_total = result.get("cart_total", cart_total)
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": user_input})
        response_text = result.get("response_text", "I didn't understand that.")
        conversation_history.append({"role": "agent", "content": response_text})
        
        # Keep history bounded (last 20 turns)
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
        
        # Speak response (print for now, TTS in production)
        print(f"Agent: {response_text}")
        print(f"[Latency: {latency:.0f}ms]\n")
        
        # Check if conversation complete (order submitted/cancelled)
        if result.get("conversation_complete"):
            print("--- Order Complete ---\n")
            # Reset for next customer
            cart_items = []
            cart_total = 0.0
            conversation_history = []


def main():
    """Entry point for voice agent."""
    run_voice_agent()


if __name__ == "__main__":
    main()
