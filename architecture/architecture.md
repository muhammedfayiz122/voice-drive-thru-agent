     +---------------------------+
     |   Customer (voice/mock)   |
     +---------------------------+
                |
                v
     +---------------------------+
     |      speech to text       |
     +---------------------------+
                |
                v
     +---------------------------+
     |         LLM               |
     +---------------------------+
                |
                v
     +---------------------------+
     |      MCP server           |
     +---------------------------+
                |
                v
     +---------------------------+
     |      Legacy menu          |
     |          +                |
     |   Inventory server        |
     +---------------------------+
                |
                v
     +---------------------------+
     |         KDS               |
     |    (order execution )     |
     +---------------------------+

### Workflow:
1. Customer speaks
2. Speech-to-Text converts voice → text
3. Agent interprets intent & updates order state
4. Agent calls MCP tools with structured inputs
5. MCP validates inputs using Pydantic
6. MCP talks to legacy menu / inventory systems
7. MCP returns normalized, deterministic responses
8. Agent decides what to say or ask next
9. When confirmed, agent calls MCP submit_order
10. MCP submits order to KDS safely


`MCP in thsi system is a middleware layer that abstracts away the complexity of interacting with legacy systems. It ensures that all inputs and outputs conform to predefined schemas, normalizes responses for consistency, and blocks any unsafe operations that could lead to errors or inconsistencies in order processing.`

```Determinism is a feature, not a limitation.```

#### MCP responsibilities:
-> Hide legacy complexity
-> Enforce schemas
-> Normalize responses
-> Block unsafe operations
-> Add business meaning
