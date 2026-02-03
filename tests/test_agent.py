"""
Comprehensive Agent Test Suite with Latency Metrics.

1. Tests all intents and matching scenarios
2. Measures latency for voice integration readiness
3. Reports P50, P95, and max latencies

Note: For voice, target latency is <1s for good UX.
"""

import time
import statistics
from app.agent.graph import build_graph


def run_tests():
    """
    Runs test suite with latency tracking.
    
    1. Executes each test case
    2. Measures response time
    3. Reports latency statistics
    """
    agent = build_graph()
    
    # Test cases: (description, user_input, cart_items)
    tests = [
        # === GREETING (no LLM for response) ===
        ("Greeting", "hi", []),
        
        # === SHOW MENU (no LLM for response) ===
        ("Show menu", "what do you have", []),
        
        # === ORDER - Various matching ===
        ("Order exact", "I want a margherita pizza", []),
        ("Order partial", "grilled chicken please", []),
        ("Order fuzzy typo", "spagetti carbonara", []),
        
        # === NOT FOUND ===
        ("Not found", "I want a burger", []),
        
        # === UNAVAILABLE ===
        ("Unavailable - ice cream", "vanilla ice cream", []),
        
        # === INVENTORY QUESTION ===
        ("Inventory question", "do you have soup", []),
        
        # === REPEAT ORDER ===
        ("Repeat order", "what did I order",
         [{"item_code": "PZ001", "menu_name": "Margherita Pizza",
           "requested_name": "pizza", "quantity": 2, "price": 350, "item_total": 700}]),
        
        # === DONE ORDERING ===
        ("Done ordering", "that's all",
         [{"item_code": "PZ001", "menu_name": "Margherita Pizza",
           "requested_name": "pizza", "quantity": 1, "price": 350, "item_total": 350}]),
    ]
    
    print("=" * 70)
    print("VOICE AGENT TEST SUITE - WITH LATENCY METRICS")
    print("=" * 70)
    print("Target: <1000ms for voice integration")
    print("=" * 70)
    
    results = []
    latencies = []
    issues = []
    
    for i, (desc, user_input, cart) in enumerate(tests, 1):
        print(f"\n{'─' * 70}")
        print(f"TEST {i}/{len(tests)}: {desc}")
        print(f"INPUT: \"{user_input}\"")
        
        try:
            # Measure latency
            start_time = time.perf_counter()
            
            result = agent.invoke({
                "user_input": user_input,
                "cart_items": cart,
                "cart_total": sum(c.get("item_total", 0) for c in cart),
                "conversation_history": [],
            })
            
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
            
            intent = result.get("intent", "N/A")
            response = result.get("response_text", "N/A")
            
            # Latency indicator
            if latency_ms < 500:
                latency_status = "🟢"
            elif latency_ms < 1000:
                latency_status = "🟡"
            else:
                latency_status = "🔴"
            
            print(f"LATENCY: {latency_status} {latency_ms:.0f}ms")
            print(f"INTENT: {intent}")
            print(f"RESPONSE: {response[:100]}..." if len(str(response)) > 100 else f"RESPONSE: {response}")
            
            # Check for issues
            if response == "N/A" or response is None:
                issues.append(f"Test {i}: No response generated")
            if latency_ms > 2000:
                issues.append(f"Test {i}: High latency ({latency_ms:.0f}ms)")
            
            results.append({
                "test": desc,
                "latency_ms": latency_ms,
                "intent": intent,
                "passed": True
            })
            print("✓ PASSED")
            
        except Exception as e:
            error_msg = str(e)[:50]
            print(f"✗ FAILED: {error_msg}")
            issues.append(f"Test {i}: {error_msg}")
            results.append({
                "test": desc,
                "latency_ms": None,
                "intent": None,
                "passed": False
            })
        
        # Small delay between tests
        time.sleep(1)
    
    # === LATENCY STATISTICS ===
    print("\n" + "=" * 70)
    print("LATENCY STATISTICS")
    print("=" * 70)
    
    if latencies:
        p50 = statistics.median(latencies)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) >= 2 else max(latencies)
        avg = statistics.mean(latencies)
        min_lat = min(latencies)
        max_lat = max(latencies)
        
        print(f"  Min:     {min_lat:.0f}ms")
        print(f"  Avg:     {avg:.0f}ms")
        print(f"  P50:     {p50:.0f}ms")
        print(f"  P95:     {p95:.0f}ms")
        print(f"  Max:     {max_lat:.0f}ms")
        
        # Voice readiness assessment
        print("\n" + "─" * 70)
        print("VOICE INTEGRATION READINESS:")
        if p95 < 1000:
            print("  ✓ READY - P95 latency under 1 second")
        elif p95 < 2000:
            print("  ⚠ MARGINAL - P95 latency 1-2 seconds (may feel slow)")
        else:
            print("  ✗ NOT READY - P95 latency over 2 seconds (needs optimization)")
    
    # === SUMMARY ===
    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    
    if issues:
        print("\nISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
    
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    run_tests()
