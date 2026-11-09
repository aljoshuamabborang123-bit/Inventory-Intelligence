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

def test_most_used_parts_returns_empty_list_when_no_usage() -> None:
    response = client.get("/analytics/most-used-parts")

    assert response.status_code == 200
    assert response.json() == []

def test_most_used_parts_ranks_by_total_quantity_used() -> None:
    def create_in_progress_work_order() -> int:
        response = client.post(
            "/work-orders",
            json={
                "title": "Analytics ranking test",
                "description": "Test most-used-parts ranking",
                "unit_number": "102",
                "priority": "high",
            },
        )

        assert response.status_code == 201
        work_order_id = response.json()["id"]

        update_response = client.put(
            f"/work-orders/{work_order_id}",
            json={
                "title": "Analytics ranking test",
                "description": "Test most-used-parts ranking",
                "unit_number": "102",
                "status": "in_progress",
                "priority": "high",
            },
        )

        assert update_response.status_code == 200
        return work_order_id

    work_order_id = create_in_progress_work_order()

    usage_records = [
        (1, 3),
        (2, 8),
        (3, 5),
    ]

    for part_id, quantity_used in usage_records:
        response = client.post(
            f"/work-orders/{work_order_id}/part-usage",
            json={
                "part_id": part_id,
                "quantity_used": quantity_used,
            },
        )

        assert response.status_code == 201

    response = client.get("/analytics/most-used-parts")

    assert response.status_code == 200

    assert response.json() == [
        {
            "part_id": 2,
            "part_name": "PVC Pipe 1/2 inch",
            "category": "plumbing",
            "total_quantity_used": 8,
        },
        {
            "part_id": 3,
            "part_name": "Electrical Outlet",
            "category": "electrical",
            "total_quantity_used": 5,
        },
        {
            "part_id": 1,
            "part_name": "LED Bulb 9W",
            "category": "electrical",
            "total_quantity_used": 3,
        },
    ]

def test_most_used_parts_respects_limit_parameter() -> None:
    work_order_response = client.post(
        "/work-orders",
        json={
            "title": "Analytics limit test",
            "description": "Test most-used-parts limit",
            "unit_number": "103",
            "priority": "high",
        },
    )

    assert work_order_response.status_code == 201
    work_order_id = work_order_response.json()["id"]

    update_response = client.put(
        f"/work-orders/{work_order_id}",
        json={
            "title": "Analytics limit test",
            "description": "Test most-used-parts limit",
            "unit_number": "103",
            "status": "in_progress",
            "priority": "high",
        },
    )

    assert update_response.status_code == 200

    for part_id, quantity_used in [(1, 3), (2, 8), (3, 5)]:
        usage_response = client.post(
            f"/work-orders/{work_order_id}/part-usage",
            json={
                "part_id": part_id,
                "quantity_used": quantity_used,
            },
        )

        assert usage_response.status_code == 201

    response = client.get("/analytics/most-used-parts?limit=2")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert [part["part_id"] for part in response.json()] == [2, 3]

def test_low_stock_returns_empty_list_when_no_parts_meet_threshold() -> None:
    response = client.get("/analytics/low-stock")

    assert response.status_code == 200
    assert response.json() == []


def test_low_stock_identifies_parts_below_custom_threshold() -> None:
    response = client.get("/analytics/low-stock?threshold=25")

    assert response.status_code == 200

    assert response.json() == [
        {
            "part_id": 3,
            "part_name": "Electrical Outlet",
            "category": "electrical",
            "current_quantity": 20,
            "threshold": 25,
        }
    ]

def test_low_stock_respects_custom_threshold_and_sorting() -> None:
    response = client.get("/analytics/low-stock?threshold=30")

    assert response.status_code == 200

    data = response.json()

    assert [part["part_id"] for part in data] == [3, 2]
    assert [part["current_quantity"] for part in data] == [20, 30]

def test_maintenance_cost_summary_returns_zero_when_empty() -> None:
    response = client.get("/analytics/maintenance-costs")

    assert response.status_code == 200

    assert response.json() == {
        "total_parts_cost": "0.00",
        "total_usage_records": 0,
        "work_orders_with_cost_count": 0,
    }

def test_maintenance_cost_summary_calculates_totals() -> None:
    def create_in_progress_work_order() -> int:
        response = client.post(
            "/work-orders",
            json={
                "title": "Maintenance cost test",
                "description": "Test maintenance expenses",
                "unit_number": "101",
                "priority": "high",
            },
        )

        assert response.status_code == 201
        work_order_id = response.json()["id"]

        update_response = client.put(
            f"/work-orders/{work_order_id}",
            json={
                "title": "Maintenance cost test",
                "description": "Test maintenance expenses",
                "unit_number": "101",
                "status": "in_progress",
                "priority": "high",
            },
        )

        assert update_response.status_code == 200

        return work_order_id

    # Set known inventory prices.
    for part_id, name, category, quantity, cost in [
        (1, "LED Bulb 9W", "electrical", 50, "85.75"),
        (2, "PVC Pipe 1/2 inch", "plumbing", 30, "120.00"),
    ]:
        response = client.put(
            f"/parts/{part_id}",
            json={
                "name": name,
                "category": category,
                "quantity": quantity,
                "unit_cost": cost,
            },
        )

        assert response.status_code == 200

    first_work_order = create_in_progress_work_order()
    second_work_order = create_in_progress_work_order()

    usage_records = [
        (first_work_order, 1, 2),
        (first_work_order, 2, 3),
        (second_work_order, 1, 1),
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

    response = client.get("/analytics/maintenance-costs")

    assert response.status_code == 200

    assert response.json() == {
        "total_parts_cost": "617.25",
        "total_usage_records": 3,
       "work_orders_with_cost_count": 2,
    }

def test_maintenance_costs_by_work_order_returns_empty_list() -> None:
    response = client.get(
        "/analytics/maintenance-costs/by-work-order"
    )

    assert response.status_code == 200
    assert response.json() == []

def test_maintenance_costs_by_category_returns_empty_list() -> None:
    response = client.get(
        "/analytics/maintenance-costs/by-category"
    )

    assert response.status_code == 200
    assert response.json() == []

def test_maintenance_costs_by_work_order_calculates_totals() -> None:
    def create_in_progress_work_order(title: str, unit_number: str) -> int:
        response = client.post(
            "/work-orders",
            json={
                "title": title,
                "description": "Test maintenance expenses",
                "unit_number": unit_number,
                "priority": "high",
            },
        )

        assert response.status_code == 201
        work_order_id = response.json()["id"]

        update_response = client.put(
            f"/work-orders/{work_order_id}",
            json={
                "title": title,
                "description": "Test maintenance expenses",
                "unit_number": unit_number,
                "status": "in_progress",
                "priority": "high",
            },
        )

        assert update_response.status_code == 200
        return work_order_id

    # Set known inventory prices.
    for part_id, name, category, quantity, cost in [
        (1, "LED Bulb 9W", "electrical", 50, "85.75"),
        (2, "PVC Pipe 1/2 inch", "plumbing", 30, "120.00"),
    ]:
        response = client.put(
            f"/parts/{part_id}",
            json={
                "name": name,
                "category": category,
                "quantity": quantity,
                "unit_cost": cost,
            },
        )
        assert response.status_code == 200

    first_work_order = create_in_progress_work_order(
        "Electrical repair",
        "101",
    )
    second_work_order = create_in_progress_work_order(
        "Plumbing repair",
        "102",
    )

    usage_records = [
        (first_work_order, 1, 2),
        (first_work_order, 2, 3),
        (second_work_order, 1, 1),
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

    response = client.get(
        "/analytics/maintenance-costs/by-work-order"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    # Most expensive work order should appear first.
    assert data[0] == {
        "work_order_id": first_work_order,
        "work_order_title": "Electrical repair",
        "unit_number": "101",
        "total_parts_cost": "531.50",
    }

    assert data[1] == {
        "work_order_id": second_work_order,
        "work_order_title": "Plumbing repair",
        "unit_number": "102",
        "total_parts_cost": "85.75",
    }

def test_maintenance_costs_by_category_calculates_totals() -> None:
    # Set known inventory prices.
    for part_id, name, category, quantity, cost in [
        (1, "LED Bulb 9W", "electrical", 50, "85.75"),
        (2, "PVC Pipe 1/2 inch", "plumbing", 30, "120.00"),
        (3, "Electrical Outlet", "electrical", 20, "50.00"),
    ]:
        response = client.put(
            f"/parts/{part_id}",
            json={
                "name": name,
                "category": category,
                "quantity": quantity,
                "unit_cost": cost,
            },
        )
        assert response.status_code == 200

    # Create an in-progress work order.
    response = client.post(
        "/work-orders",
        json={
            "title": "Category cost test",
            "description": "Test category expenses",
            "unit_number": "101",
            "priority": "high",
        },
    )
    assert response.status_code == 201

    work_order_id = response.json()["id"]

    update_response = client.put(
        f"/work-orders/{work_order_id}",
        json={
            "title": "Category cost test",
            "description": "Test category expenses",
            "unit_number": "101",
            "status": "in_progress",
            "priority": "high",
        },
    )
    assert update_response.status_code == 200

    usage_records = [
        (1, 2),
        (2, 3),
        (3, 4),
    ]

    for part_id, quantity_used in usage_records:
        response = client.post(
            f"/work-orders/{work_order_id}/part-usage",
            json={
                "part_id": part_id,
                "quantity_used": quantity_used,
            },
        )
        assert response.status_code == 201

    response = client.get(
        "/analytics/maintenance-costs/by-category"
    )

    assert response.status_code == 200

    assert response.json() == [
        {
            "category": "electrical",
            "total_parts_cost": "371.50",
        },
        {
            "category": "plumbing",
            "total_parts_cost": "360.00",
        },
    ]