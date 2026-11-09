from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_unit():
    response = client.post(
        "/units",
        json={
            "building_name": "Building A",
            "unit_number": "101",
            "floor_number": 1,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["building_name"] == "Building A"
    assert data["unit_number"] == "101"
    assert data["floor_number"] == 1
    assert data["status"] == "vacant"
    assert data["id"] == 1


def test_create_unit_with_explicit_status():
    response = client.post(
        "/units",
        json={
            "building_name": "Building B",
            "unit_number": "201",
            "floor_number": 2,
            "status": "occupied",
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "occupied"

def test_create_duplicate_unit_returns_409():
    payload = {
        "building_name": "Building A",
        "unit_number": "101",
    }

    first_response = client.post("/units", json=payload)
    second_response = client.post("/units", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "A unit with this building name and unit number already exists."
    )

def test_same_unit_number_allowed_in_different_buildings():
    first_response = client.post(
        "/units",
        json={
            "building_name": "Building A",
            "unit_number": "101",
        },
    )

    second_response = client.post(
        "/units",
        json={
            "building_name": "Building B",
            "unit_number": "101",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

def test_get_units():
    client.post(
        "/units",
        json={
            "building_name": "Building A",
            "unit_number": "102",
        },
    )

    client.post(
        "/units",
        json={
            "building_name": "Building A",
            "unit_number": "101",
        },
    )

    response = client.get("/units")

    assert response.status_code == 200
    assert len(response.json()) == 2

    unit_numbers = [
        unit["unit_number"]
        for unit in response.json()
    ]

    assert unit_numbers == ["101", "102"]

def test_get_units_with_filters():
    client.post(
        "/units",
        json={
            "building_name": "Building A",
            "unit_number": "101",
            "floor_number": 1,
            "status": "occupied",
        },
    )

    client.post(
        "/units",
        json={
            "building_name": "Building A",
            "unit_number": "201",
            "floor_number": 2,
            "status": "vacant",
        },
    )

    response = client.get(
        "/units",
        params={
            "building_name": "building a",
            "status": "occupied",
            "floor_number": 1,
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["unit_number"] == "101"

def test_get_unit_by_id():
    create_response = client.post(
        "/units",
        json={
            "building_name": "Building A",
            "unit_number": "101",
        },
    )

    unit_id = create_response.json()["id"]

    response = client.get(f"/units/{unit_id}")

    assert response.status_code == 200
    assert response.json()["id"] == unit_id
    assert response.json()["building_name"] == "Building A"
    assert response.json()["unit_number"] == "101"

def test_get_nonexistent_unit_returns_404():
    response = client.get("/units/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Unit not found."

def test_update_unit():
    create_response = client.post(
        "/units",
        json={
            "building_name": "Building A",
            "unit_number": "101",
            "floor_number": 1,
            "status": "vacant",
        },
    )

    unit_id = create_response.json()["id"]

    response = client.put(
        f"/units/{unit_id}",
        json={
            "building_name": "Building A",
            "unit_number": "101",
            "floor_number": 1,
            "status": "occupied",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "occupied"
    assert response.json()["unit_number"] == "101"

def test_update_nonexistent_unit_returns_404():
    response = client.put(
        "/units/999",
        json={
            "building_name": "Building A",
            "unit_number": "101",
            "floor_number": 1,
            "status": "occupied",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Unit not found."

def test_update_unit_to_duplicate_combination_returns_409():
    client.post(
        "/units",
        json={
            "building_name": "Building A",
            "unit_number": "101",
        },
    )

    second_response = client.post(
        "/units",
        json={
            "building_name": "Building A",
            "unit_number": "102",
        },
    )

    second_unit_id = second_response.json()["id"]

    response = client.put(
        f"/units/{second_unit_id}",
        json={
            "building_name": "Building A",
            "unit_number": "101",
            "floor_number": 1,
            "status": "occupied",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "A unit with this building name and unit number already exists."
    )