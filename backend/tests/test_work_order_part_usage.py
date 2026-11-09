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