from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def create_in_progress_work_order() -> int:
    response = client.post(
        "/work-orders",
        json={
            "title": "Repair bathroom plumbing",
            "description": "Replace damaged pipe",
            "unit_number": "101",
            "priority": "high",
        },
    )

    assert response.status_code == 201

    work_order = response.json()

    update_response = client.put(
        f"/work-orders/{work_order['id']}",
        json={
            "title": "Repair bathroom plumbing",
            "description": "Replace damaged pipe",
            "unit_number": "101",
            "status": "in_progress",
            "priority": "high",
        },
    )

    assert update_response.status_code == 200

    return work_order["id"]


def test_record_part_usage_reduces_inventory() -> None:
    work_order_id = create_in_progress_work_order()

    response = client.post(
        f"/work-orders/{work_order_id}/part-usage",
        json={
            "part_id": 1,
            "quantity_used": 3,
        },
    )

    assert response.status_code == 201

    usage = response.json()

    assert usage["work_order_id"] == work_order_id
    assert usage["part_id"] == 1
    assert usage["quantity_used"] == 3
    assert usage["recorded_at"] is not None

    part_response = client.get("/parts/1")

    assert part_response.status_code == 200
    assert part_response.json()["quantity"] == 47


def test_record_part_usage_rejects_zero_quantity() -> None:
    work_order_id = create_in_progress_work_order()

    response = client.post(
        f"/work-orders/{work_order_id}/part-usage",
        json={
            "part_id": 1,
            "quantity_used": 0,
        },
    )

    assert response.status_code == 422


def test_record_part_usage_rejects_insufficient_stock() -> None:
    work_order_id = create_in_progress_work_order()

    response = client.post(
        f"/work-orders/{work_order_id}/part-usage",
        json={
            "part_id": 1,
            "quantity_used": 1000,
        },
    )

    assert response.status_code == 409

    part_response = client.get("/parts/1")

    assert part_response.json()["quantity"] == 50


def test_record_part_usage_rejects_work_order_not_in_progress() -> None:
    response = client.post(
        "/work-orders",
        json={
            "title": "Inspect electrical outlet",
            "description": "Check outlet condition",
            "unit_number": "102",
            "priority": "medium",
        },
    )

    work_order_id = response.json()["id"]

    usage_response = client.post(
        f"/work-orders/{work_order_id}/part-usage",
        json={
            "part_id": 1,
            "quantity_used": 2,
        },
    )

    assert usage_response.status_code == 409

    part_response = client.get("/parts/1")

    assert part_response.json()["quantity"] == 50


def test_record_part_usage_rejects_missing_work_order() -> None:
    response = client.post(
        "/work-orders/99999/part-usage",
        json={
            "part_id": 1,
            "quantity_used": 2,
        },
    )

    assert response.status_code == 404


def test_record_part_usage_rejects_missing_part() -> None:
    work_order_id = create_in_progress_work_order()

    response = client.post(
        f"/work-orders/{work_order_id}/part-usage",
        json={
            "part_id": 99999,
            "quantity_used": 2,
        },
    )

    assert response.status_code == 404

def test_get_work_order_part_usage_returns_history() -> None:
    work_order_id = create_in_progress_work_order()

    first_usage = client.post(
        f"/work-orders/{work_order_id}/part-usage",
        json={
            "part_id": 1,
            "quantity_used": 3,
        },
    )

    second_usage = client.post(
        f"/work-orders/{work_order_id}/part-usage",
        json={
            "part_id": 2,
            "quantity_used": 5,
        },
    )

    assert first_usage.status_code == 201
    assert second_usage.status_code == 201

    response = client.get(
        f"/work-orders/{work_order_id}/part-usage"
    )

    assert response.status_code == 200

    history = response.json()

    assert len(history) == 2
    assert history[0]["part_id"] == 1
    assert history[0]["quantity_used"] == 3
    assert history[1]["part_id"] == 2
    assert history[1]["quantity_used"] == 5

def test_get_work_order_part_usage_returns_empty_list() -> None:
    work_order_id = create_in_progress_work_order()

    response = client.get(
        f"/work-orders/{work_order_id}/part-usage"
    )

    assert response.status_code == 200
    assert response.json() == []

def test_delete_part_with_usage_history_returns_conflict() -> None:
    work_order_id = create_in_progress_work_order()

    usage_response = client.post(
        f"/work-orders/{work_order_id}/part-usage",
        json={
            "part_id": 1,
            "quantity_used": 2,
        },
    )

    assert usage_response.status_code == 201

    delete_response = client.delete("/parts/1")

    assert delete_response.status_code == 409
    assert delete_response.json()["detail"] == (
        "Cannot delete part because it has recorded usage history"
    )

    part_response = client.get("/parts/1")

    assert part_response.status_code == 200
    assert part_response.json()["quantity"] == 48

def test_delete_work_order_with_usage_history_returns_conflict() -> None:
    work_order_id = create_in_progress_work_order()

    usage_response = client.post(
        f"/work-orders/{work_order_id}/part-usage",
        json={
            "part_id": 1,
            "quantity_used": 2,
        },
    )

    assert usage_response.status_code == 201

    delete_response = client.delete(
        f"/work-orders/{work_order_id}"
    )

    assert delete_response.status_code == 409
    assert delete_response.json()["detail"] == (
        "Cannot delete work order because it has recorded parts usage"
    )

    history_response = client.get(
        f"/work-orders/{work_order_id}/part-usage"
    )

    assert history_response.status_code == 200
    assert len(history_response.json()) == 1

    assert history_response.json()[0]["quantity_used"] == 2
