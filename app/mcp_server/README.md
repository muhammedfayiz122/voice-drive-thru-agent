# MCP Server (Model Control Plane)

## Overview

The MCP Server acts as a **deterministic control and safety layer** between an AI Agent and existing backend systems.

Its primary responsibility is to ensure that **probabilistic AI behavior never directly interacts with critical business systems** such as legacy menu, inventory, or kitchen systems.

In this project, the MCP Server protects the legacy menu and inventory system and provides a **safe, normalized, and policy-driven interface** for the AI agent.

---

## Why MCP Is Required

AI agents:

* Can hallucinate items
* Can generate invalid quantities
* Can make unsafe or unintended requests

Legacy systems:

* Are reliable but **assume trusted, human-driven inputs**
* Are not designed for autonomous or probabilistic callers

The MCP Server exists to **bridge this mismatch** by enforcing strict rules, validations, and boundaries.

---

## Responsibilities of MCP

The MCP Server is responsible for:

1. Validating all AI-generated inputs
2. Preventing hallucinated or invalid actions
3. Normalizing legacy system data into clean, AI-friendly formats
4. Enforcing business and safety rules
5. Acting as the **single gateway** to backend systems

The AI Agent **never** talks directly to the legacy system or KDS.

---

## Architecture Position

```
AI Agent (LangGraph / LLM)
        |
        v
MCP Server (FastAPI)
        |
        v
Legacy Menu & Inventory System
```

---

## Internal Structure

The MCP Server is intentionally kept simple and explicit.

```
mcp_server/
├── api.py            # Public MCP API (gatekeeper)
├── legacy_client.py # Raw communication with legacy systems
├── validators.py    # Deterministic business & safety rules
└── README.md
```

---

## Component Responsibilities

### `legacy_client.py`

* Communicates with the legacy menu and inventory system
* Fetches raw data without validation or interpretation
* Assumes legacy responses may be inconsistent or incomplete

This file isolates all legacy-specific behavior.

---

### `validators.py`

* Enforces deterministic rules that the AI agent cannot bypass
* Prevents hallucinated items and invalid quantities
* Applies machine-dependent availability checks

This layer is critical for AI safety and production readiness.

---

### `api.py`

* Exposes clean, restrictive MCP APIs
* Coordinates validation, legacy access, and decision-making
* Returns **decisions**, not raw legacy data

This file represents the public contract of the MCP Server.

---

## Exposed MCP APIs

### Get Clean Menu

```
GET /mcp/menu
```

Returns a normalized menu suitable for AI consumption.

---

### Check Item Availability

```
GET /mcp/inventory/{item_code}
```

Returns a decision-based response:

* Whether the item is available
* The reason if unavailable

---

### Submit Order

```
POST /mcp/order
```

Validates the order and safely forwards it to downstream systems (e.g., KDS).

---

## Design Principles

* **Deterministic over probabilistic**
* **Explicit rules over implicit assumptions**
* **Few, restrictive APIs over many flexible ones**
* **Clear separation of concerns**

The MCP Server is intentionally simple to ensure it is auditable, explainable, and safe.

---

## Assumptions & Scope

* Inventory mutation is handled downstream (e.g., POS or ERP systems)
* MCP performs read-only validation against inventory
* KDS integration is mocked for this task

These choices are intentional to keep responsibilities well-defined.

---

## How to Run

```bash
uvicorn api:app --port 8000
```

Ensure the legacy system is running before starting MCP.

---

## Summary

The MCP Server demonstrates how AI systems can be safely integrated with existing infrastructure by introducing a strict control plane that enforces validation, policy, and trust boundaries.

This approach reflects real-world AI automation practices and avoids relying on model intelligence alone for system safety.
