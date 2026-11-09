from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_dashboard_summary_returns_baseline_metrics() -> None:
    response = client.get("/dashboard/summary")

    assert response.status_code == 200

    data = response.json()

    # Inventory metrics from the three seeded parts.
    assert data["inventory"]["total_parts"] == 3
    assert data["inventory"]["total_stock_quantity"] == 100
    assert Decimal(data["inventory"]["total_inventory_value"]) == Decimal("0.00")
    assert data["inventory"]["low_stock_count"] == 0
    assert data["inventory"]["out_of_stock_count"] == 0
    assert data["inventory"]["low_stock_threshold"] == 10

    # No units have been created.
    assert data["units"]["total_units"] == 0
    assert data["units"]["occupancy_rate"] == 0.0

    # No work orders have been created.
    assert data["work_orders"]["total_work_orders"] == 0

    # No maintenance tasks have been created.
    assert data["maintenance_tasks"]["total_tasks"] == 0
    assert data["maintenance_tasks"]["overdue_tasks"] == 0

    # No part usage has been recorded.
    assert Decimal(data["costs"]["total_parts_cost"]) == Decimal("0.00")
    assert data["costs"]["total_usage_records"] == 0
    assert data["costs"]["work_orders_with_cost_count"] == 0

def test_dashboard_summary_applies_custom_low_stock_threshold() -> None:
    response = client.get(
        "/dashboard/summary",
        params={"low_stock_threshold": 30},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["inventory"]["low_stock_threshold"] == 30
    assert data["inventory"]["low_stock_count"] == 2
    assert data["inventory"]["out_of_stock_count"] == 0

def test_dashboard_summary_calculates_unit_occupancy() -> None:
    units = [
        {"building_name": "Building A", "unit_number": "101", "status": "occupied"},
        {"building_name": "Building A", "unit_number": "102", "status": "occupied"},
        {"building_name": "Building A", "unit_number": "103", "status": "vacant"},
        {
            "building_name": "Building B",
            "unit_number": "201",
            "status": "under_maintenance",
        },
        {"building_name": "Building B", "unit_number": "202", "status": "turnover"},
    ]

    for unit in units:
        response = client.post("/units", json=unit)
        assert response.status_code == 201

    response = client.get("/dashboard/summary")

    assert response.status_code == 200

    data = response.json()
    unit_metrics = data["units"]

    assert unit_metrics["total_units"] == 5
    assert unit_metrics["occupied_units"] == 2
    assert unit_metrics["vacant_units"] == 1
    assert unit_metrics["under_maintenance_units"] == 1
    assert unit_metrics["turnover_units"] == 1
    assert unit_metrics["occupancy_rate"] == 40.0

def test_dashboard_summary_calculates_work_order_metrics() -> None:
    work_orders = [
        {
            "title": "Repair 101",
            "description": "Repair unit 101.",
            "unit_number": "101",
            "priority": "high",
        },
        {
            "title": "Repair 102",
            "description": "Repair unit 102.",
            "unit_number": "102",
            "priority": "urgent",
        },
        {
            "title": "Repair 103",
            "description": "Repair unit 103.",
            "unit_number": "103",
            "priority": "medium",
        },
        {
            "title": "Repair 104",
            "description": "Repair unit 104.",
            "unit_number": "104",
            "priority": "high",
        },
    ]

    expected_statuses = [
        "open",
        "in_progress",
        "completed",
        "cancelled",
    ]

    for index, (work_order, status) in enumerate(
        zip(work_orders, expected_statuses)
    ):
        response = client.post("/work-orders", json=work_order)
        assert response.status_code == 201, response.text

        work_order_id = response.json()["id"]

        if status == "in_progress":
            update_payload = {**work_order, "status": "in_progress"}

            update_response = client.put(
                f"/work-orders/{work_order_id}",
                json=update_payload,
            )
            assert update_response.status_code == 200, update_response.text

        elif status == "completed":
            update_payload = {**work_order, "status": "in_progress"}

            start_response = client.put(
                f"/work-orders/{work_order_id}",
                json=update_payload,
            )
            assert start_response.status_code == 200, start_response.text

            update_payload["status"] = "completed"

            complete_response = client.put(
                f"/work-orders/{work_order_id}",
                json=update_payload,
            )
            assert complete_response.status_code == 200, complete_response.text

        elif status == "cancelled":
            update_payload = {**work_order, "status": "cancelled"}

            cancel_response = client.put(
                f"/work-orders/{work_order_id}",
                json=update_payload,
            )
            assert cancel_response.status_code == 200, cancel_response.text

def test_dashboard_summary_calculates_maintenance_task_metrics() -> None:
    unit_response = client.post(
        "/units",
        json={
            "building_name": "Building A",
            "unit_number": "101",
        },
    )
    assert unit_response.status_code == 201

    unit_id = unit_response.json()["id"]

    tasks = [
        {
            "title": "Pending repair",
            "description": "Repair bathroom faucet.",
            "category": "repair",
            "priority": "high",
            "assigned_to": "Technician A",
            "due_date": "2026-11-08",
        },
        {
            "title": "Ongoing inspection",
            "description": "Inspect electrical wiring.",
            "category": "inspection",
            "priority": "urgent",
            "assigned_to": " ",
            "due_date": "2026-11-08",
        },
        {
            "title": "Completed cleaning",
            "description": "Clean vacant apartment.",
            "category": "cleaning",
            "priority": "medium",
            "assigned_to": "Technician B",
            "due_date": "2026-11-08",
        },
        {
            "title": "Cancelled repair",
            "description": "Repair damaged door.",
            "category": "repair",
            "priority": "high",
            "assigned_to": None,
            "due_date": "2026-11-08",
        },
    ]

    expected_statuses = [
        "pending",
        "in_progress",
        "completed",
        "cancelled",
    ]

    for task, status in zip(tasks, expected_statuses):
        create_response = client.post(
            "/maintenance-tasks",
            json={**task, "unit_id": unit_id},
        )
        assert create_response.status_code == 201, create_response.text

        if status != "pending":
            task_id = create_response.json()["id"]

            update_response = client.put(
                f"/maintenance-tasks/{task_id}",
                json={**task, "unit_id": unit_id, "status": status},
            )
            assert update_response.status_code == 200, update_response.text

    response = client.get("/dashboard/summary")

    assert response.status_code == 200

    metrics = response.json()["maintenance_tasks"]

    assert metrics["total_tasks"] == 4
    assert metrics["pending_tasks"] == 1
    assert metrics["in_progress_tasks"] == 1
    assert metrics["completed_tasks"] == 1
    assert metrics["cancelled_tasks"] == 1
    assert metrics["overdue_tasks"] == 2
    assert metrics["unassigned_tasks"] == 2
    assert metrics["high_priority_tasks"] == 2
    assert metrics["urgent_priority_tasks"] == 1

def test_dashboard_summary_calculates_recorded_parts_cost() -> None:
    # Set the current price of the seeded LED Bulb.
    part_response = client.put(
        "/parts/1",
        json={
            "name": "LED Bulb 9W",
            "category": "electrical",
            "quantity": 50,
            "unit_cost": "25.50",
        },
    )
    assert part_response.status_code == 200, part_response.text

    work_order_response = client.post(
        "/work-orders",
        json={
            "title": "Electrical repair",
            "description": "Replace LED bulbs.",
            "unit_number": "101",
            "priority": "high",
        },
    )
    assert work_order_response.status_code == 201

    work_order_id = work_order_response.json()["id"]

    # Move the work order to in_progress.
    update_response = client.put(
        f"/work-orders/{work_order_id}",
        json={
            "title": "Electrical repair",
            "description": "Replace LED bulbs.",
            "unit_number": "101",
            "status": "in_progress",
            "priority": "high",
        },
    )
    assert update_response.status_code == 200

    # Record usage: 3 bulbs × 25.50 = 76.50.
    usage_response = client.post(
        f"/work-orders/{work_order_id}/part-usage",
        json={
            "part_id": 1,
            "quantity_used": 3,
        },
    )
    assert usage_response.status_code == 201, usage_response.text

    response = client.get("/dashboard/summary")

    assert response.status_code == 200

    costs = response.json()["costs"]

    assert Decimal(costs["total_parts_cost"]) == Decimal("76.50")
    assert costs["total_usage_records"] == 1
    assert costs["work_orders_with_cost_count"] == 1