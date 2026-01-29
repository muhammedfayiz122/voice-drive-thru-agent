from fastapi import FastAPI, HTTPException
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

app = FastAPI()

@app.get("/legacy/menu")
async def get_menu():
    try:
        with open(DATA_DIR / "menu.json", 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Menu file missing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/legacy/inventory")
async def get_full_inventory():
    try:
        with open(DATA_DIR / "inventory.json", 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Inventory file missing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/legacy/inventory/{item_code}")
async def get_inventory(item_code: str):
    try:
        with open(DATA_DIR / "inventory.json", 'r') as file:
            inventory = json.load(file)
        stock = inventory.get("stock_levels", {})
        return {
            "item_code": item_code, 
            "stock": stock.get(item_code)
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Inventory file missing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    