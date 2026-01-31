START
  ↓
LLM_INTENT_ANALYSIS
  ↓
DECIDE_INTENT
  |
  ├──GREETING→ GREETING_RESPONSE → END
  | eg.: "Hello! -> Welcome to FastFood Express. How can I assist you today?" -> END
  |
  ├──ORDER→ INVENTORY_CHECK → CONFIRM(Human-in-the-loop) (if not user provided confirmation , then give this input to LLM_INTENT_ANALYSIS node as restart, whatd o you think of this?) -> confirm response → SUBMIT
  | eg.: "I'd like to order a burger and fries." -> "your order is a burger and fries, is that correct?" -> "yes" -> "Order submitted! Your food will be ready shortly."-> END
  |
  ├──QUERY→ INVENTORY_CHECK → INVENTORY_RESPONSE  → CONFIRM → END
  | eg.: "Do you have vegan options?" -> "Yes, we have a vegan burger and salad." -> END
  |
  ├──INVALID→ LLM_CLARIFY_RESPONSE → END
  | eg.: "Blah blah blah" -> "I'm sorry, I didn't understand that. Could you please rephrase?" -> END

or

START
  ↓
LLM_INTENT_ANALYSIS
  ↓
DECIDE_INTENT
  ├── GREETING → LLM_RESPONSE → END
  ├── ORDER → INVENTORY_CHECK → CONFIRM → SUBMIT
  ├── QUERY → MCP_QUERY → LLM_RESPONSE → END
  ├── INVALID → LLM_CLARIFY_RESPONSE → END

or

START
  ↓
LLM_INTENT_ANALYSIS
  ↓
DECIDE_INTENT
  ├── GREETING → GREETING_RESPONSE → END
  ├── ORDER → INVENTORY_CHECK → CONFIRM → SUBMIT
  ├── QUERY → MCP_QUERY → INVENTORY_RESPONSE → END
  ├── INVALID → LLM_CLARIFY_RESPONSE → END

or

START
  ↓
LLM_INTENT_ANALYSIS
  ↓
DECIDE_INTENT
  |
  ├──GREETING→ GREETING_RESPONSE → END
  |
  ├──ORDER/QUERY → INVENTORY_CHECK 
  |                     ├──unavailable→ LLM_RESPONSE → END
  |                     ├──available→ CONFIRM -> SUBMIT -> END
  |
  |
  ├──INVALID→ LLM_CLARIFY_RESPONSE → END