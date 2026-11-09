from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def create_test_unit() -> int:
    response = client.post(
        "/units",
        json={
            "building_name": "Building A",
            "unit_number": "101",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]

def test_create_unit_turn():
    unit_id = create_test_unit()

    response = client.post(
        "/unit-turns",
        json={
            "unit_id": unit_id,
            "move_out_date": "2026-11-09",
            "notes": "Tenant moved out.",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["unit_id"] == unit_id
    assert data["move_out_date"] == "2026-11-09"
    assert data["status"] == "pending"
    assert data["started_at"] is None
    assert data["completed_at"] is None
    assert data["notes"] == "Tenant moved out."

def test_create_unit_turn_with_nonexistent_unit_returns_404():
    response = client.post(
        "/unit-turns",
        json={
            "unit_id": 999,
            "move_out_date": "2026-11-09",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Unit not found."

def test_create_second_active_unit_turn_returns_409():
    unit_id = create_test_unit()

    payload = {
        "unit_id": unit_id,
        "move_out_date": "2026-11-09",
    }

    first_response = client.post("/unit-turns", json=payload)
    second_response = client.post("/unit-turns", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "This unit already has an active turnover."
    )

def test_get_unit_turns():
    unit_id = create_test_unit()

    client.post(
        "/unit-turns",
        json={
            "unit_id": unit_id,
            "move_out_date": "2026-11-08",
        },
    )

    first_turn = client.get("/unit-turns").json()[0]

    complete_response = client.put(
        f"/unit-turns/{first_turn['id']}",
        json={
            "move_out_date": "2026-11-08",
            "status": "completed",
        },
    )

    assert complete_response.status_code == 200

    client.post(
        "/unit-turns",
        json={
            "unit_id": unit_id,
            "move_out_date": "2026-11-09",
        },
    )

    response = client.get("/unit-turns")

    assert response.status_code == 200
    assert len(response.json()) == 2

    dates = [
        turn["move_out_date"]
        for turn in response.json()
    ]

    assert dates == ["2026-11-09", "2026-11-08"]

def test_get_unit_turns_filtered_by_unit_id():
    first_unit_id = create_test_unit()

    second_unit_response = client.post(
        "/units",
        json={
            "building_name": "Building B",
            "unit_number": "201",
        },
    )

    assert second_unit_response.status_code == 201

    second_unit_id = second_unit_response.json()["id"]

    for unit_id, move_out_date in [
        (first_unit_id, "2026-11-08"),
        (second_unit_id, "2026-11-09"),
    ]:
        client.post(
            "/unit-turns",
            json={
                "unit_id": unit_id,
                "move_out_date": move_out_date,
            },
        )

    response = client.get(
        "/unit-turns",
        params={"unit_id": first_unit_id},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["unit_id"] == first_unit_id

def test_get_unit_turns_filtered_by_status():
    unit_id = create_test_unit()

    create_response = client.post(
        "/unit-turns",
        json={
            "unit_id": unit_id,
            "move_out_date": "2026-11-08",
        },
    )

    assert create_response.status_code == 201

    turn_id = create_response.json()["id"]

    client.put(
        f"/unit-turns/{turn_id}",
        json={
            "move_out_date": "2026-11-08",
            "status": "completed",
        },
    )

    response = client.get(
        "/unit-turns",
        params={"status": "completed"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "completed"

def test_get_unit_turn_by_id():
    unit_id = create_test_unit()

    create_response = client.post(
        "/unit-turns",
        json={
            "unit_id": unit_id,
            "move_out_date": "2026-11-09",
        },
    )

    assert create_response.status_code == 201

    turn_id = create_response.json()["id"]

    response = client.get(f"/unit-turns/{turn_id}")

    assert response.status_code == 200
    assert response.json()["id"] == turn_id
    assert response.json()["unit_id"] == unit_id

def test_get_nonexistent_unit_turn_returns_404():
    response = client.get("/unit-turns/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Unit turn not found."

def test_start_unit_turn_sets_started_at():
    unit_id = create_test_unit()

    create_response = client.post(
        "/unit-turns",
        json={
            "unit_id": unit_id,
            "move_out_date": "2026-11-09",
        },
    )

    turn_id = create_response.json()["id"]

    response = client.put(
        f"/unit-turns/{turn_id}",
        json={
            "move_out_date": "2026-11-09",
            "status": "in_progress",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "in_progress"
    assert data["started_at"] is not None
    assert data["completed_at"] is None

def test_complete_unit_turn_sets_completed_at():
    unit_id = create_test_unit()

    create_response = client.post(
        "/unit-turns",
        json={
            "unit_id": unit_id,
            "move_out_date": "2026-11-09",
        },
    )

    turn_id = create_response.json()["id"]

    start_response = client.put(
        f"/unit-turns/{turn_id}",
        json={
            "move_out_date": "2026-11-09",
            "status": "in_progress",
        },
    )

    started_at = start_response.json()["started_at"]

    response = client.put(
        f"/unit-turns/{turn_id}",
        json={
            "move_out_date": "2026-11-09",
            "status": "completed",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "completed"
    assert data["started_at"] == started_at
    assert data["completed_at"] is not None

def test_completed_unit_turn_cannot_be_reopened():
    unit_id = create_test_unit()

    create_response = client.post(
        "/unit-turns",
        json={
            "unit_id": unit_id,
            "move_out_date": "2026-11-09",
        },
    )

    turn_id = create_response.json()["id"]

    complete_response = client.put(
        f"/unit-turns/{turn_id}",
        json={
            "move_out_date": "2026-11-09",
            "status": "completed",
        },
    )

    assert complete_response.status_code == 200

    reopen_response = client.put(
        f"/unit-turns/{turn_id}",
        json={
            "move_out_date": "2026-11-09",
            "status": "in_progress",
        },
    )

    assert reopen_response.status_code == 409
    assert reopen_response.json()["detail"] == (
        "This turnover status transition is not allowed."
    )

def test_cancelled_unit_turn_cannot_be_reopened():
    unit_id = create_test_unit()

    create_response = client.post(
        "/unit-turns",
        json={
            "unit_id": unit_id,
            "move_out_date": "2026-11-09",
        },
    )

    turn_id = create_response.json()["id"]

    cancel_response = client.put(
        f"/unit-turns/{turn_id}",
        json={
            "move_out_date": "2026-11-09",
            "status": "cancelled",
        },
    )

    assert cancel_response.status_code == 200

    reopen_response = client.put(
        f"/unit-turns/{turn_id}",
        json={
            "move_out_date": "2026-11-09",
            "status": "pending",
        },
    )

    assert reopen_response.status_code == 409
    assert reopen_response.json()["detail"] == (
        "This turnover status transition is not allowed."
    )

def test_new_unit_turn_allowed_after_previous_turn_completed():
    unit_id = create_test_unit()

    first_response = client.post(
        "/unit-turns",
        json={
            "unit_id": unit_id,
            "move_out_date": "2026-11-08",
        },
    )

    first_turn_id = first_response.json()["id"]

    complete_response = client.put(
        f"/unit-turns/{first_turn_id}",
        json={
            "move_out_date": "2026-11-08",
            "status": "completed",
        },
    )

    assert complete_response.status_code == 200

    second_response = client.post(
        "/unit-turns",
        json={
            "unit_id": unit_id,
            "move_out_date": "2026-11-09",
        },
    )

    assert second_response.status_code == 201
    assert second_response.json()["status"] == "pending"