"""Quick test for fuzzy matching and key scenarios."""

from app.agent.graph import build_graph

agent = build_graph()

tests = [
    ("Partial match", "grilled chicken", []),
    ("Fuzzy/typo", "spagetti", []),
    ("Not on menu", "burger", []),
    ("Ice cream (broken)", "ice cream", []),
]

for desc, inp, cart in tests:
    print(f"--- {desc}: \"{inp}\" ---")
    result = agent.invoke({
        "user_input": inp,
        "cart_items": cart,
        "cart_total": 0,
        "conversation_history": [],
    })
    print(f"Intent: {result.get('intent')}")
    print(f"Response: {result.get('response_text')}")
    if result.get("cart_items"):
        print(f"Cart: {[c['menu_name'] for c in result['cart_items']]}")
    print()
