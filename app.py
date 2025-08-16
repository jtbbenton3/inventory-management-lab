from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

inventory = [
    {
        "id": 1,
        "name": "Organic Almond Milk",
        "brand": "Silk",
        "price": 4.99,
        "stock": 30,
        "sku": "ALM-ORG-32OZ",
        "barcode": "1234567890123",
        "ingredients_text": "Filtered water, almonds, cane sugar",
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

HTTP_HEADERS = {
    "User-Agent": "inventory-management-lab/0.1 (+https://github.com/jtbbenton3/inventory-management-lab)"
}
HTTP_TIMEOUT = 8


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


def get_json(url, params=None):
    try:
        resp = requests.get(url, params=params, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    except requests.RequestException:
        return None, 502, {"error": "failed to fetch"}
    if resp.status_code != 200:
        return None, 502, {"error": "failed to fetch"}
    try:
        return resp.json(), 200, None
    except ValueError:
        return None, 502, {"error": "invalid response from upstream"}


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/inventory", methods=["GET"])
def list_inventory():
    return jsonify(inventory)


@app.route("/inventory/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = next((i for i in inventory if i["id"] == item_id), None)
    if item is None:
        return jsonify({"error": f"item {item_id} not found"}), 404
    return jsonify(item)


@app.route("/inventory", methods=["POST"])
def create_item():
    data = request.get_json()
    errors = validate_item(data)
    if errors:
        return jsonify({"errors": errors}), 400
    new_id = max((i["id"] for i in inventory), default=0) + 1
    data["id"] = new_id
    inventory.append(data)
    return jsonify(data), 201


@app.route("/inventory/<int:item_id>", methods=["PATCH"])
def update_item(item_id):
    data = request.get_json()
    item = next((i for i in inventory if i["id"] == item_id), None)
    if item is None:
        return jsonify({"error": f"item {item_id} not found"}), 404
    item.update(data)
    return jsonify(item)


@app.route("/inventory/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    global inventory
    item = next((i for i in inventory if i["id"] == item_id), None)
    if item is None:
        return jsonify({"error": f"item {item_id} not found"}), 404
    inventory = [i for i in inventory if i["id"] != item_id]
    return "", 204


@app.route("/external/barcode/<barcode>", methods=["GET"])
def fetch_by_barcode(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    data, code, err = get_json(url)
    if err:
        return jsonify(err), code
    if data.get("status") != 1:
        return jsonify({"error": "product not found"}), 404
    product = data["product"]
    return jsonify(
        {
            "barcode": barcode,
            "name": product.get("product_name"),
            "brand": product.get("brands"),
            "ingredients_text": product.get("ingredients_text"),
        }
    )


@app.route("/external/search", methods=["GET"])
def search_products():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "query param q required"}), 400
    url = "https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 10,
        "fields": "id,product_name,brands",
    }
    data, code, err = get_json(url, params=params)
    if err:
        return jsonify(err), code
    products = data.get("products", [])
    results = []
    for p in products[:5]:
        results.append(
            {
                "barcode": p.get("id"),
                "name": p.get("product_name"),
                "brand": p.get("brands"),
            }
        )
    return jsonify(results)


@app.route("/inventory/enrich/<barcode>", methods=["POST"])
def enrich_item(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    data, code, err = get_json(url)
    if err:
        return jsonify(err), code
    if data.get("status") != 1:
        return jsonify({"error": "product not found"}), 404
    product = data["product"]
    new_id = max((i["id"] for i in inventory), default=0) + 1
    item = {
        "id": new_id,
        "name": product.get("product_name"),
        "brand": product.get("brands"),
        "price": 0.0,
        "stock": 0,
        "sku": "",
        "barcode": barcode,
        "ingredients_text": product.get("ingredients_text"),
    }
    inventory.append(item)
    return jsonify(item), 201


if __name__ == "__main__":
    app.run(port=5555, debug=True)