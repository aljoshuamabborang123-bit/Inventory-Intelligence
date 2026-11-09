from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_parts_consumption_summary_returns_zero_when_empty() -> None:
    response = client.get("/analytics/parts-consumption")

    assert response.status_code == 200

    data = response.json()

    assert data == {
        "total_quantity_consumed": 0,
        "unique_parts_count": 0,
        "work_orders_with_usage_count": 0,
        "consumption_by_category": [],
    }

def test_parts_consumption_summary_calculates_totals() -> None:
    def create_in_progress_work_order() -> int:
        response = client.post(
            "/work-orders",
            json={
                "title": "Maintenance repair",
                "description": "Test analytics consumption",
                "unit_number": "101",
                "priority": "high",
            },
        )

        assert response.status_code == 201
        work_order_id = response.json()["id"]

        update_response = client.put(
            f"/work-orders/{work_order_id}",
            json={
                "title": "Maintenance repair",
                "description": "Test analytics consumption",
                "unit_number": "101",
                "status": "in_progress",
                "priority": "high",
            },
        )

        assert update_response.status_code == 200

        return work_order_id

    first_work_order = create_in_progress_work_order()
    second_work_order = create_in_progress_work_order()

    usage_records = [
        (first_work_order, 1, 3),
        (first_work_order, 2, 5),
        (second_work_order, 1, 2),
        (second_work_order, 3, 4),
    ]

    for work_order_id, part_id, quantity_used in usage_records:
        response = client.post(
            f"/work-orders/{work_order_id}/part-usage",
            json={
                "part_id": part_id,
                "quantity_used": quantity_used,
            },
        )

        assert response.status_code == 201

    response = client.get("/analytics/parts-consumption")

    assert response.status_code == 200

    data = response.json()

    assert data["total_quantity_consumed"] == 14
    assert data["unique_parts_count"] == 3
    assert data["work_orders_with_usage_count"] == 2

    assert data["consumption_by_category"] == [
        {
            "category": "electrical",
            "total_quantity_used": 9,
        },
        {
            "category": "plumbing",
            "total_quantity_used": 5,
        },
    ]