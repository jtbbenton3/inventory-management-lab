import pytest
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}

def test_list_inventory(client):
    res = client.get("/inventory")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) >= 3

def test_get_item_success(client):
    res = client.get("/inventory/1")
    assert res.status_code == 200
    assert "name" in res.get_json()

def test_get_item_not_found(client):
    res = client.get("/inventory/99999")
    assert res.status_code == 404
    assert "error" in res.get_json()

def test_add_item(client):
    res = client.post("/inventory", json={
        "name": "Test Item",
        "brand": "Test Brand",
        "price": 1.99,
        "stock": 10
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["name"] == "Test Item"

def test_update_item(client):
    res = client.patch("/inventory/1", json={"stock": 50})
    assert res.status_code == 200
    data = res.get_json()
    assert data["stock"] == 50

def test_delete_item(client):
    res = client.delete("/inventory/2")
    assert res.status_code in (200, 204, 404)  # allow already deleted

def test_external_barcode(client):
    res = client.get("/external/barcode/737628064502")  # Coca-Cola barcode
    assert res.status_code in (200, 404, 502)  # allow API failures
    assert "error" in res.get_json() or "name" in res.get_json()

def test_external_search(client):
    res = client.get("/external/search?q=milk")
    assert res.status_code in (200, 502)