# Voice Agent - Latency Optimization Guide

## The Problem

Voice agents have ONE job: **respond fast**.

Target latency for voice UX:
- **< 500ms** = Excellent (feels instant)
- **< 1000ms** = Good (acceptable)
- **> 2000ms** = Bad (user thinks it's broken)

Our initial implementation had **P95 of 11 seconds**. Unacceptable.

---

## Root Cause Analysis

| Operation | Latency | Why |
|-----------|---------|-----|
| LLM Intent Analysis | ~800ms | Unavoidable - need to understand user |
| MCP Menu Fetch | ~500ms | Called on EVERY request |
| MCP Validation | ~500ms | Called on EVERY order |
| MCP Suggestions | ~500ms | Called when item not found |
| **Total (worst case)** | **~11s** | Death by a thousand cuts |

---

## Fix 1 — Cache MCP Results

### Never call MCP in the request path unless forced.

```python
# BAD - Called on every request
def order_handler(state):
    menu = mcp_client.get_menu()  # 500ms wasted
    result = validate_order(items)  # Another 500ms
    ...

# GOOD - Use cached data
class MenuCache:
    _menu = None
    _inventory = None
    _last_refresh = 0
    
    @classmethod
    def get_menu(cls):
        if cls._menu is None:
            cls._refresh()
        return cls._menu
    
    @classmethod  
    def _refresh(cls):
        # Called once at startup, then every 60s
        cls._menu = mcp_client.get_menu()
        cls._inventory = mcp_client.get_inventory()
```

### What to cache:
- **Menu** → Load once at startup (changes rarely)
- **Inventory** → Periodic sync every 30-60 seconds
- **Suggestions** → Compute locally from cached menu

---

## Fix 2 — Kill "Validate Before Responding" Thinking

### The wrong mental model:
```
User says "burger" 
  → Call MCP to validate 
  → Wait for response 
  → Then respond to user
```

### The right mental model:
```
User says "burger"
  → Check local cache instantly
  → Respond immediately
  → (Optional) Validate in background
```

### Real drive-thru systems speculate fast and correct later.

When you order at McDonald's:
1. Cashier says "One Big Mac" immediately
2. They don't wait for inventory system to confirm
3. If out of stock, they tell you AFTER

**Speed > Perfect accuracy** for voice UX.

---

## Fix 3 — Parallelize If You MUST Call External Services

If you absolutely must call MCP during a request:

```python
# BAD - Sequential
result = await validate_order()      # 500ms
response = await prepare_response()  # 300ms
# Total: 800ms

# GOOD - Parallel  
result, response = await asyncio.gather(
    validate_order(),
    prepare_response(),
)
# Total: 500ms (max of the two)
```

**But honestly: don't call MCP in the request path at all.**

---

## Implementation Checklist

- [ ] Create `MenuCache` singleton loaded at startup
- [ ] Move fuzzy matching to use cached menu
- [ ] Remove MCP calls from `show_menu_node` (use cache)
- [ ] Remove MCP calls from `order_handler` validation (use cache)
- [ ] Remove `get_similar_items` MCP call (use cache)
- [ ] Add background task to refresh cache every 60s
- [ ] Only call MCP for final order submission (unavoidable)

---

## Target Latency After Optimization

| Operation | Before | After |
|-----------|--------|-------|
| Greeting | 980ms | ~800ms (LLM only) |
| Show Menu | 4800ms | ~800ms (LLM + cache read) |
| Order | 7000ms | ~900ms (LLM + cache lookup) |
| Not Found | 11000ms | ~900ms (LLM + cache similarity) |
| **P95** | **11s** | **<1.5s** |

---

## Key Principle

> "The fastest API call is the one you don't make."

Cache aggressively. Speculate confidently. Correct gracefully.
