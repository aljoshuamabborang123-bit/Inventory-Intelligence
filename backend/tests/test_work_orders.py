from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_all_work_orders() -> None:
    response = client.get("/work-orders")

    assert response.status_code == 200
    assert response.json() == []


def test_filter_work_orders_by_status() -> None:
    response = client.get("/work-orders?status=open")

    assert response.status_code == 200
    assert response.json() == []


def test_filter_work_orders_by_priority() -> None:
    response = client.get("/work-orders?priority=urgent")

    assert response.status_code == 200
    assert response.json() == []


def test_work_orders_reject_invalid_status() -> None:
    response = client.get("/work-orders?status=invalid")

    assert response.status_code == 422


def test_work_orders_reject_invalid_priority() -> None:
    response = client.get("/work-orders?priority=invalid")

    assert response.status_code == 422


def test_work_orders_limit_below_minimum_is_rejected() -> None:
    response = client.get("/work-orders?limit=0")

    assert response.status_code == 422


def test_work_orders_limit_above_maximum_is_rejected() -> None:
    response = client.get("/work-orders?limit=101")

    assert response.status_code == 422

def test_create_work_order() -> None:
    payload = {
        "title": "Repair leaking bathroom faucet",
        "description": "Replace the damaged faucet cartridge.",
        "unit_number": "A-101",
        "priority": "high",
    }

    response = client.post("/work-orders", json=payload)

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert data["unit_number"] == payload["unit_number"]
    assert data["status"] == "open"
    assert data["priority"] == "high"
    assert isinstance(data["id"], int)
    assert data["created_at"] is not None
    assert data["updated_at"] is not None
    assert data["completed_at"] is None


def test_create_work_order_uses_default_priority() -> None:
    payload = {
        "title": "Inspect electrical outlet",
        "description": "Check the outlet for damage.",
        "unit_number": "B-205",
    }

    response = client.post("/work-orders", json=payload)

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "open"
    assert data["priority"] == "medium"

def test_get_work_order_by_id() -> None:
    payload = {
        "title": "Repair kitchen sink",
        "description": "Fix the leaking kitchen sink.",
        "unit_number": "A-102",
        "priority": "high",
    }

    create_response = client.post("/work-orders", json=payload)

    assert create_response.status_code == 201

    work_order_id = create_response.json()["id"]

    response = client.get(f"/work-orders/{work_order_id}")

    assert response.status_code == 200
    assert response.json()["id"] == work_order_id
    assert response.json()["title"] == payload["title"]

def test_get_work_order_not_found() -> None:
    response = client.get("/work-orders/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Work order not found"

def test_update_work_order() -> None:
    payload = {
        "title": "Repair kitchen sink",
        "description": "Fix the leaking kitchen sink.",
        "unit_number": "A-102",
        "priority": "high",
    }

    create_response = client.post("/work-orders", json=payload)
    work_order_id = create_response.json()["id"]

    update_payload = {
        "title": "Repair kitchen sink - completed",
        "description": "Replaced the damaged faucet cartridge.",
        "unit_number": "A-102",
        "status": "in_progress",
        "priority": "urgent",
    }

    response = client.put(
        f"/work-orders/{work_order_id}",
        json=update_payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == update_payload["title"]
    assert data["status"] == "in_progress"
    assert data["priority"] == "urgent"
    assert data["completed_at"] is None


def test_update_work_order_not_found() -> None:
    payload = {
        "title": "Unknown work order",
        "description": "This record does not exist.",
        "unit_number": "A-999",
        "status": "in_progress",
        "priority": "medium",
    }

    response = client.put("/work-orders/999", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Work order not found"


def test_complete_work_order_sets_completed_at() -> None:
    payload = {
        "title": "Repair bathroom faucet",
        "description": "Replace the damaged faucet cartridge.",
        "unit_number": "B-101",
    }

    create_response = client.post("/work-orders", json=payload)
    work_order_id = create_response.json()["id"]

    update_payload = {
        "title": payload["title"],
        "description": payload["description"],
        "unit_number": payload["unit_number"],
        "status": "in_progress",
        "priority": "medium",
    }

    start_response = client.put(
        f"/work-orders/{work_order_id}",
        json=update_payload,
    )

    assert start_response.status_code == 200

    update_payload["status"] = "completed"

    response = client.put(
        f"/work-orders/{work_order_id}",
        json=update_payload,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["completed_at"] is not None

def test_completed_work_order_cannot_be_reopened() -> None:
    payload = {
        "title": "Repair damaged outlet",
        "description": "Replace damaged electrical outlet.",
        "unit_number": "C-101",
    }

    create_response = client.post("/work-orders", json=payload)
    work_order_id = create_response.json()["id"]

    update_payload = {
        "title": payload["title"],
        "description": payload["description"],
        "unit_number": payload["unit_number"],
        "status": "in_progress",
        "priority": "medium",
    }

    client.put(f"/work-orders/{work_order_id}", json=update_payload)

    update_payload["status"] = "completed"
    client.put(f"/work-orders/{work_order_id}", json=update_payload)

    update_payload["status"] = "open"

    response = client.put(
        f"/work-orders/{work_order_id}",
        json=update_payload,
    )

    assert response.status_code == 409
    assert "Cannot change status" in response.json()["detail"]


def test_cancelled_work_order_cannot_be_reopened() -> None:
    payload = {
        "title": "Inspect broken pipe",
        "description": "Inspect reported pipe damage.",
        "unit_number": "C-102",
    }

    create_response = client.post("/work-orders", json=payload)
    work_order_id = create_response.json()["id"]

    update_payload = {
        "title": payload["title"],
        "description": payload["description"],
        "unit_number": payload["unit_number"],
        "status": "cancelled",
        "priority": "medium",
    }

    client.put(f"/work-orders/{work_order_id}", json=update_payload)

    update_payload["status"] = "in_progress"

    response = client.put(
        f"/work-orders/{work_order_id}",
        json=update_payload,
    )

    assert response.status_code == 409

def test_delete_work_order() -> None:
    payload = {
        "title": "Repair leaking faucet",
        "description": "Replace the damaged faucet.",
        "unit_number": "A-101",
    }

    create_response = client.post("/work-orders", json=payload)
    work_order_id = create_response.json()["id"]

    response = client.delete(f"/work-orders/{work_order_id}")

    assert response.status_code == 204
    assert response.content == b""

    get_response = client.get(f"/work-orders/{work_order_id}")

    assert get_response.status_code == 404


def test_delete_work_order_not_found() -> None:
    response = client.delete("/work-orders/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Work order not found"

def test_work_orders_are_sorted_by_priority() -> None:
    priorities = ["low", "urgent", "medium", "high"]

    for priority in priorities:
        response = client.post(
            "/work-orders",
            json={
                "title": f"{priority.title()} priority repair",
                "description": "Test priority sorting.",
                "unit_number": "A-101",
                "priority": priority,
            },
        )
        assert response.status_code == 201

    response = client.get("/work-orders")

    assert response.status_code == 200

    returned_priorities = [
        work_order["priority"] for work_order in response.json()
    ]

    assert returned_priorities == [
        "urgent",
        "high",
        "medium",
        "low",
    ]