# Legacy Menu & Inventory System

## Overview

This service simulates an existing **legacy menu and inventory system** used internally by a fast-food chain.

The system represents an **old, unsafe, and non–AI-aware backend** that was not designed to be accessed by modern AI agents directly.

Its purpose in this project is to demonstrate why an **MCP (Model Control Plane) Server** is required as a protective and translation layer before allowing AI access.

---

## Key Characteristics of This Legacy System

* No authentication or authorization
* Exposes raw internal data structures
* Poorly designed APIs
* No input validation
* No business logic enforcement
* Tight coupling between data and API responses

This is intentional and reflects common real-world legacy systems.

---

## Architecture Role

```
AI Agent  ❌  (NO DIRECT ACCESS)
    |
    v
MCP Server  ✅  (Validation, policy, safety)
    |
    v
Legacy System  ⚠️ (This service)
```

The AI Agent must **never** call this service directly.

---

## Available Endpoints

### Get Full Menu

```
GET /legacy/menu
```

Returns the raw menu data exactly as stored.

---

### Get Full Inventory

```
GET /legacy/inventory
```

Returns raw inventory data including machine status and stock levels.

---

### Get Inventory by Item Code

```
GET /legacy/inventory/{item_code}
```

Returns stock information for a specific item code.

Example response:

```json
{
  "item_code": "ICE09",
  "stock": 0
}
```

---

## Data Storage

Data is stored locally in JSON files:

```
data/
├── menu.json
└── inventory.json
```

This simulates file-based or database-backed legacy systems commonly found in older infrastructure.

---

## Important Notes

* This service performs **no validation**
* Invalid or missing data may be returned as-is
* Error handling is minimal
* This is intentional to highlight the risks of direct AI access

---

## Why MCP Is Required

Because this legacy system:

* Can return inconsistent data
* Does not protect against hallucinated inputs
* Can be misused by autonomous agents

An MCP Server is required to:

* Validate inputs
* Normalize responses
* Enforce safety rules
* Protect the legacy backend

---

## Running the Service

```bash
uvicorn server:app --port 7000
```

---

## Disclaimer

This service is intentionally designed to be **unsafe and unpolished** to accurately represent real-world legacy systems.
