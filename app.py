from flask import Flask, jsonify, request
from typing import List, Dict, Any, Optional

MOCK_INVENTORY: List[Dict[str, Any]] = [
    {
        "id": 1,
        "sku": "ALM-ORG-32OZ",
        "name": "Organic Almond Milk",
        "brand": "Silk",
        "price": 4.99,
        "stock": 24,
        "barcode": "1234567890123",
        "ingredients_text": "Filtered water, almonds, cane sugar",
    },
    {
        "id": 2,
        "sku": "OAT-PLN-32OZ",
        "name": "Plain Oat Milk",
        "brand": "Oatly",
        "price": 5.49,
        "stock": 12,
        "barcode": "2345678901234",
        "ingredients_text": "Water, oats, rapeseed oil",
    },
    {
        "id": 3,
        "sku": "PB-CRNCH-16OZ",
        "name": "Crunchy Peanut Butter",
        "brand": "Justin's",
        "price": 6.99,
        "stock": 8,
        "barcode": "3456789012345",
        "ingredients_text": "Dry roasted peanuts, palm oil",
    },
]

def _next_id(items: List[Dict[str, Any]]) -> int:
    return (max((i["id"] for i in items), default=0) + 1) if items else 1

def _find_item(items: List[Dict[str, Any]], item_id: int) -> Optional[Dict[str, Any]]:
    for it in items:
        if it["id"] == item_id:
            return it
    return None

def create_app():
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.get("/inventory")
    def list_inventory():
        return jsonify(MOCK_INVENTORY), 200

    @app.get("/inventory/<int:item_id>")
    def get_inventory_item(item_id: int):
        item = _find_item(MOCK_INVENTORY, item_id)
        if not item:
            return jsonify({"error": f"item {item_id} not found"}), 404
        return jsonify(item), 200

    @app.post("/inventory")
    def create_inventory_item():
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 415
        data = request.get_json(silent=True) or {}

        errors = []
        if not isinstance(data.get("name"), str) or not data.get("name"):
            errors.append("name (string) is required")
        if not isinstance(data.get("brand"), str) or not data.get("brand"):
            errors.append("brand (string) is required")

        price = data.get("price")
        try:
            price = float(price)
        except (TypeError, ValueError):
            errors.append("price (number) is required")

        stock = data.get("stock")
        try:
            stock = int(stock)
            if stock < 0:
                errors.append("stock must be >= 0")
        except (TypeError, ValueError):
            errors.append("stock (integer) is required")

        if errors:
            return jsonify({"errors": errors}), 400

        new_item = {
            "id": _next_id(MOCK_INVENTORY),
            "sku": data.get("sku") or "",
            "name": data["name"],
            "brand": data["brand"],
            "price": price,
            "stock": stock,
            "barcode": data.get("barcode") or "",
            "ingredients_text": data.get("ingredients_text") or "",
        }
        MOCK_INVENTORY.append(new_item)
        return jsonify(new_item), 201

    @app.patch("/inventory/<int:item_id>")
    def update_inventory_item(item_id: int):
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 415

        item = _find_item(MOCK_INVENTORY, item_id)
        if not item:
            return jsonify({"error": f"item {item_id} not found"}), 404

        data = request.get_json(silent=True) or {}
        allowed = {"name", "brand", "price", "stock", "sku", "barcode", "ingredients_text"}
        unknown = [k for k in data.keys() if k not in allowed]
        if unknown:
            return jsonify({"errors": [f"unknown field: {k}" for k in unknown]}), 400

        errors = []

        if "name" in data:
            if not isinstance(data["name"], str) or not data["name"]:
                errors.append("name must be a non-empty string")
        if "brand" in data:
            if not isinstance(data["brand"], str) or not data["brand"]:
                errors.append("brand must be a non-empty string")
        if "price" in data:
            try:
                data["price"] = float(data["price"])
            except (TypeError, ValueError):
                errors.append("price must be a number")
        if "stock" in data:
            try:
                data["stock"] = int(data["stock"])
                if data["stock"] < 0:
                    errors.append("stock must be >= 0")
            except (TypeError, ValueError):
                errors.append("stock must be an integer")
        for key in ("sku", "barcode", "ingredients_text"):
            if key in data and data[key] is not None and not isinstance(data[key], str):
                errors.append(f"{key} must be a string")

        if errors:
            return jsonify({"errors": errors}), 400

        for k, v in data.items():
            item[k] = v

        return jsonify(item), 200

    @app.delete("/inventory/<int:item_id>")
    def delete_inventory_item(item_id: int):
        item = _find_item(MOCK_INVENTORY, item_id)
        if not item:
            return jsonify({"error": f"item {item_id} not found"}), 404
        MOCK_INVENTORY.remove(item)
        return ("", 204)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(port=5555, debug=True)