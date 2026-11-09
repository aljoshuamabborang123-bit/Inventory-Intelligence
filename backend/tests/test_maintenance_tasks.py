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

def create_test_work_order() -> int:
    response = client.post(
        "/work-orders",
        json={
            "title": "Bathroom Repair",
            "description": "Repair leaking bathroom pipe.",
            "unit_number": "101",
            "priority": "medium",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]

def test_create_maintenance_task():
    unit_id = create_test_unit()

    response = client.post(
        "/maintenance-tasks",
        json={
            "unit_id": unit_id,
            "title": "Replace bathroom faucet",
            "description": "Replace the leaking bathroom faucet.",
            "category": "repair",
            "priority": "high",
            "assigned_to": "Maintenance Technician",
            "due_date": "2026-11-15",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["unit_id"] == unit_id
    assert data["title"] == "Replace bathroom faucet"
    assert data["category"] == "repair"
    assert data["status"] == "pending"
    assert data["priority"] == "high"
    assert data["assigned_to"] == "Maintenance Technician"
    assert data["due_date"] == "2026-11-15"
    assert data["completed_at"] is None

def test_create_maintenance_task_with_unit_turn():
    unit_id = create_test_unit()

    turn_response = client.post(
        "/unit-turns",
        json={
            "unit_id": unit_id,
            "move_out_date": "2026-11-09",
            "notes": "Tenant moved out.",
        },
    )

    assert turn_response.status_code == 201

    unit_turn_id = turn_response.json()["id"]

    response = client.post(
        "/maintenance-tasks",
        json={
            "unit_id": unit_id,
            "unit_turn_id": unit_turn_id,
            "title": "Inspect bathroom",
            "description": "Inspect plumbing during turnover.",
            "category": "inspection",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["unit_id"] == unit_id
    assert data["unit_turn_id"] == unit_turn_id
    assert data["status"] == "pending"

def test_create_maintenance_task_with_work_order():
    unit_id = create_test_unit()
    work_order_id = create_test_work_order()

    response = client.post(
        "/maintenance-tasks",
        json={
            "unit_id": unit_id,
            "work_order_id": work_order_id,
            "title": "Replace electrical outlet",
            "description": "Replace damaged wall outlet.",
            "category": "repair",
            "priority": "urgent",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["unit_id"] == unit_id
    assert data["work_order_id"] == work_order_id
    assert data["title"] == "Replace electrical outlet"
    assert data["priority"] == "urgent"

def test_create_maintenance_task_with_nonexistent_unit_returns_404():
    response = client.post(
        "/maintenance-tasks",
        json={
            "unit_id": 999,
            "title": "Repair door",
            "description": "Fix damaged apartment door.",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Unit not found."

def test_create_maintenance_task_with_nonexistent_unit_turn_returns_404():
    unit_id = create_test_unit()

    response = client.post(
        "/maintenance-tasks",
        json={
            "unit_id": unit_id,
            "unit_turn_id": 999,
            "title": "Inspect kitchen",
            "description": "Inspect kitchen fixtures.",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Unit turn not found."

def test_create_maintenance_task_with_unit_turn_from_another_unit_returns_409():
    first_unit_id = create_test_unit()

    second_unit_response = client.post(
        "/units",
        json={
            "building_name": "Building B",
            "unit_number": "202",
        },
    )

    assert second_unit_response.status_code == 201

    second_unit_id = second_unit_response.json()["id"]

    turn_response = client.post(
        "/unit-turns",
        json={
            "unit_id": second_unit_id,
            "move_out_date": "2026-11-09",
        },
    )

    assert turn_response.status_code == 201

    unit_turn_id = turn_response.json()["id"]

    response = client.post(
        "/maintenance-tasks",
        json={
            "unit_id": first_unit_id,
            "unit_turn_id": unit_turn_id,
            "title": "Inspect plumbing",
            "description": "Inspect plumbing fixtures.",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "The unit turn does not belong to the specified unit."
    )

def test_create_maintenance_task_with_nonexistent_work_order_returns_404():
    unit_id = create_test_unit()

    response = client.post(
        "/maintenance-tasks",
        json={
            "unit_id": unit_id,
            "work_order_id": 999,
            "title": "Repair ceiling",
            "description": "Repair damaged ceiling.",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Work order not found."

def test_get_maintenance_tasks():
    unit_id = create_test_unit()

    client.post(
        "/maintenance-tasks",
        json={
            "unit_id": unit_id,
            "title": "Clean kitchen",
            "description": "Clean kitchen surfaces.",
            "category": "cleaning",
        },
    )

    response = client.get(
        "/maintenance-tasks",
        params={"unit_id": unit_id},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["unit_id"] == unit_id
    assert data[0]["title"] == "Clean kitchen"

def test_get_maintenance_task():
    unit_id = create_test_unit()

    create_response = client.post(
        "/maintenance-tasks",
        json={
            "unit_id": unit_id,
            "title": "Check smoke detector",
            "description": "Test smoke detector functionality.",
            "category": "inspection",
        },
    )

    assert create_response.status_code == 201

    task_id = create_response.json()["id"]

    response = client.get(f"/maintenance-tasks/{task_id}")

    assert response.status_code == 200
    assert response.json()["id"] == task_id
    assert response.json()["title"] == "Check smoke detector"

def test_get_nonexistent_maintenance_task_returns_404():
    response = client.get("/maintenance-tasks/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Maintenance task not found."

def test_update_maintenance_task():
    unit_id = create_test_unit()

    create_response = client.post(
        "/maintenance-tasks",
        json={
            "unit_id": unit_id,
            "title": "Repair kitchen sink",
            "description": "Check leaking kitchen sink.",
        },
    )

    assert create_response.status_code == 201

    task_id = create_response.json()["id"]

    response = client.put(
        f"/maintenance-tasks/{task_id}",
        json={
            "title": "Replace kitchen sink",
            "description": "Replace damaged kitchen sink.",
            "category": "repair",
            "status": "in_progress",
            "priority": "high",
            "assigned_to": "Maintenance Technician",
            "due_date": "2026-11-15",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == task_id
    assert data["unit_id"] == unit_id
    assert data["title"] == "Replace kitchen sink"
    assert data["status"] == "in_progress"
    assert data["priority"] == "high"
    assert data["completed_at"] is None

def test_complete_maintenance_task_sets_completed_at():
    unit_id = create_test_unit()

    create_response = client.post(
        "/maintenance-tasks",
        json={
            "unit_id": unit_id,
            "title": "Repair bathroom faucet",
            "description": "Replace leaking faucet.",
        },
    )

    assert create_response.status_code == 201

    task_id = create_response.json()["id"]

    response = client.put(
        f"/maintenance-tasks/{task_id}",
        json={
            "title": "Repair bathroom faucet",
            "description": "Replace leaking faucet.",
            "category": "repair",
            "status": "completed",
            "priority": "medium",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "completed"
    assert data["completed_at"] is not None

def test_completed_maintenance_task_cannot_be_reopened():
    unit_id = create_test_unit()

    create_response = client.post(
        "/maintenance-tasks",
        json={
            "unit_id": unit_id,
            "title": "Inspect electrical outlet",
            "description": "Check outlet safety.",
        },
    )

    task_id = create_response.json()["id"]

    complete_response = client.put(
        f"/maintenance-tasks/{task_id}",
        json={
            "title": "Inspect electrical outlet",
            "description": "Check outlet safety.",
            "category": "inspection",
            "status": "completed",
            "priority": "medium",
        },
    )

    assert complete_response.status_code == 200

    update_response = client.put(
        f"/maintenance-tasks/{task_id}",
        json={
            "title": "Inspect electrical outlet",
            "description": "Check outlet safety.",
            "category": "inspection",
            "status": "in_progress",
            "priority": "medium",
        },
    )

    assert update_response.status_code == 409
    assert update_response.json()["detail"] == (
        "This maintenance task status transition is not allowed."
    )

def test_update_nonexistent_maintenance_task_returns_404():
    response = client.put(
        "/maintenance-tasks/999",
        json={
            "title": "Repair door",
            "description": "Fix damaged door.",
            "category": "repair",
            "status": "in_progress",
            "priority": "medium",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Maintenance task not found."
