from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

inventory = [
    {
        "id": 1,
        "name": "Organic Almond Milk",
        "brand": "Silk",
        "price": 4.99,
        "stock": 24,
        "sku": "ALM-ORG-32OZ",
        "barcode": "1234567890123",
        "ingredients_text": "Filtered water, almonds, cane sugar",
    },
    {
        "id": 2,
        "name": "Plain Oat Milk",
        "brand": "Oatly",
        "price": 5.49,
        "stock": 12,
        "sku": "OAT-PLN-32OZ",
        "barcode": "2345678901234",
        "ingredients_text": "Water, oats, rapeseed oil",
    },
    {
        "id": 3,
        "name": "Crunchy Peanut Butter",
        "brand": "Justin's",
        "price": 6.99,
        "stock": 8,
        "sku": "PB-CRNCH-16OZ",
        "barcode": "3456789012345",
        "ingredients_text": "Dry roasted peanuts, palm oil",
    },
]

def validate_item(data):
    errors = []
    if not data.get("name") or not isinstance(data.get("name"), str):
        errors.append("name (string) is required")
    if not data.get("brand") or not isinstance(data.get("brand"), str):
        errors.append("brand (string) is required")
    if not isinstance(data.get("price"), (int, float)):
        errors.append("price (number) is required")
    if not isinstance(data.get("stock"), int):
        errors.append("stock (integer) is required")
    return errors

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/inventory", methods=["GET"])
def list_inventory():
    return jsonify(inventory)

@app.route("/inventory/<int:item_id>", methods=["GET"])
def get_item(item_id):
    for item in inventory:
        if item["id"] == item_id:
            return jsonify(item)
    return jsonify({"error": f"item {item_id} not found"}), 404

@app.route("/inventory", methods=["POST"])
def add_item():
    data = request.get_json()
    errors = validate_item(data)
    if errors:
        return jsonify({"errors": errors}), 400
    new_id = max([i["id"] for i in inventory], default=0) + 1
    item = {
        "id": new_id,
        "name": data["name"],
        "brand": data["brand"],
        "price": float(data["price"]),
        "stock": int(data["stock"]),
        "sku": data.get("sku", ""),
        "barcode": data.get("barcode", ""),
        "ingredients_text": data.get("ingredients_text", ""),
    }
    inventory.append(item)
    return jsonify(item), 201

@app.route("/inventory/<int:item_id>", methods=["PATCH"])
def update_item(item_id):
    data = request.get_json()
    for item in inventory:
        if item["id"] == item_id:
            item.update({k: v for k, v in data.items() if k in item})
            return jsonify(item)
    return jsonify({"error": f"item {item_id} not found"}), 404

@app.route("/inventory/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    global inventory
    for item in inventory:
        if item["id"] == item_id:
            inventory = [i for i in inventory if i["id"] != item_id]
            return "", 204
    return jsonify({"error": f"item {item_id} not found"}), 404

@app.route("/external/barcode/<barcode>", methods=["GET"])
def external_barcode(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    try:
        resp = requests.get(url, headers={"User-Agent": "inventory-app/1.0"}, timeout=5)
        data = resp.json()
    except Exception:
        return jsonify({"error": "failed to fetch product"}), 502
    if data.get("status") != 1:
        return jsonify({"error": f"barcode {barcode} not found"}), 404
    product = data.get("product", {})
    return jsonify({
        "barcode": barcode,
        "name": product.get("product_name", ""),
        "brand": product.get("brands", ""),
        "ingredients_text": product.get("ingredients_text", ""),
    })

@app.route("/external/search", methods=["GET"])
def external_search():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "q param is required"}), 400
    url = "https://world.openfoodfacts.org/cgi/search.pl"
    params = {"search_terms": query, "search_simple": 1, "action": "process", "json": 1, "page_size": 5}
    try:
        resp = requests.get(url, headers={"User-Agent": "inventory-app/1.0"}, params=params, timeout=5)
        data = resp.json()
    except Exception:
        return jsonify({"error": "failed to search products"}), 502
    products = data.get("products", [])
    return jsonify([
        {
            "barcode": p.get("id", ""),
            "name": p.get("product_name", ""),
            "brand": p.get("brands", ""),
            "ingredients_text": p.get("ingredients_text", ""),
        }
        for p in products
    ])

@app.route("/inventory/enrich/<barcode>", methods=["POST"])
def enrich_item(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    try:
        resp = requests.get(url, headers={"User-Agent": "inventory-app/1.0"}, timeout=5)
        data = resp.json()
    except Exception:
        return jsonify({"error": "failed to fetch product"}), 502
    if data.get("status") != 1:
        return jsonify({"error": f"barcode {barcode} not found"}), 404
    product = data.get("product", {})
    new_id = max([i["id"] for i in inventory], default=0) + 1
    item = {
        "id": new_id,
        "name": product.get("product_name", ""),
        "brand": product.get("brands", ""),
        "price": 0.0,
        "stock": 0,
        "sku": "",
        "barcode": barcode,
        "ingredients_text": product.get("ingredients_text", ""),
    }
    inventory.append(item)
    return jsonify(item), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5555)