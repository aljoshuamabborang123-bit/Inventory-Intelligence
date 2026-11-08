from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_all_parts() -> None:
    response = client.get("/parts")

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_filter_parts_by_category() -> None:
    response = client.get("/parts?category=electrical")

    assert response.status_code == 200
    assert len(response.json()) == 2

    for part in response.json():
        assert part["category"] == "electrical"


def test_limit_parts_results() -> None:
    response = client.get("/parts?limit=1")

    assert response.status_code == 200
    assert len(response.json()) == 1
def test_limit_below_minimum_is_rejected() -> None:
    response = client.get("/parts?limit=0")

    assert response.status_code == 422


def test_limit_above_maximum_is_rejected() -> None:
    response = client.get("/parts?limit=101")

    assert response.status_code == 422

def test_create_part() -> None:
    payload = {
        "name": "Test LED Bulb",
        "category": "electrical",
        "quantity": 25,
    }

    response = client.post("/parts", json=payload)

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test LED Bulb"
    assert data["category"] == "electrical"
    assert data["quantity"] == 25
    assert isinstance(data["id"], int)


def test_create_part_rejects_missing_name() -> None:
    payload = {
        "category": "electrical",
        "quantity": 25,
    }

    response = client.post("/parts", json=payload)

    assert response.status_code == 422

def test_get_part_by_id() -> None:
    response = client.get("/parts/1")

    assert response.status_code == 200
    assert response.json()["name"] == "LED Bulb 9W"
    assert response.json()["id"] == 1


def test_get_part_not_found() -> None:
    response = client.get("/parts/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Part not found"

def test_update_part() -> None:
    payload = {
        "name": "PVC Pipe 3/4 inch",
        "category": "plumbing",
        "quantity": 45,
    }

    response = client.put("/parts/2", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 2
    assert data["name"] == "PVC Pipe 3/4 inch"
    assert data["category"] == "plumbing"
    assert data["quantity"] == 45


def test_update_part_not_found() -> None:
    payload = {
        "name": "Unknown Part",
        "category": "electrical",
        "quantity": 10,
    }

    response = client.put("/parts/999", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Part not found"

def test_delete_part() -> None:
    response = client.delete("/parts/3")

    assert response.status_code == 204
    assert response.content == b""

    get_response = client.get("/parts/3")
    assert get_response.status_code == 404


def test_delete_part_not_found() -> None:
    response = client.delete("/parts/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Part not found"