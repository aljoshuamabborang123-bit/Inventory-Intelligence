from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def create_test_unit(
    building_name: str = "Building A",
    unit_number: str = "101",
) -> int:
    response = client.post(
        "/units",
        json={
            "building_name": building_name,
            "unit_number": unit_number,
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_test_task(
    unit_id: int,
    title: str = "Test maintenance task",
    assigned_to: str | None = None,
    due_date: str | None = None,
) -> int:
    response = client.post(
        "/maintenance-tasks",
        json={
            "unit_id": unit_id,
            "title": title,
            "description": "Test task description.",
            "assigned_to": assigned_to,
            "due_date": due_date,
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def update_task_status(task_id: int, status: str) -> None:
    response = client.get(f"/maintenance-tasks/{task_id}")

    assert response.status_code == 200

    task = response.json()

    update_response = client.put(
        f"/maintenance-tasks/{task_id}",
        json={
            "title": task["title"],
            "description": task["description"],
            "category": task["category"],
            "status": status,
            "priority": task["priority"],
            "assigned_to": task["assigned_to"],
            "due_date": task["due_date"],
        },
    )

    assert update_response.status_code == 200


def test_maintenance_task_summary():
    unit_id = create_test_unit()

    pending_id = create_test_task(unit_id, "Pending task")
    in_progress_id = create_test_task(unit_id, "In-progress task")
    completed_id = create_test_task(unit_id, "Completed task")
    cancelled_id = create_test_task(unit_id, "Cancelled task")

    update_task_status(in_progress_id, "in_progress")
    update_task_status(completed_id, "completed")
    update_task_status(cancelled_id, "cancelled")

    response = client.get("/analytics/maintenance-tasks/summary")

    assert response.status_code == 200
    assert response.json() == {
        "total_tasks": 4,
        "pending_tasks": 1,
        "in_progress_tasks": 1,
        "completed_tasks": 1,
        "cancelled_tasks": 1,
    }


def test_maintenance_task_summary_when_empty():
    response = client.get("/analytics/maintenance-tasks/summary")

    assert response.status_code == 200
    assert response.json() == {
        "total_tasks": 0,
        "pending_tasks": 0,
        "in_progress_tasks": 0,
        "completed_tasks": 0,
        "cancelled_tasks": 0,
    }

def test_maintenance_task_completion_rate():
    unit_id = create_test_unit()

    completed_id = create_test_task(unit_id, "Completed task")
    create_test_task(unit_id, "Pending task")
    cancelled_id = create_test_task(unit_id, "Cancelled task")

    update_task_status(completed_id, "completed")
    update_task_status(cancelled_id, "cancelled")

    response = client.get(
        "/analytics/maintenance-tasks/completion-rate"
    )

    assert response.status_code == 200
    assert response.json() == {
        "total_tasks": 3,
        "completed_tasks": 1,
        "completion_rate": 33.33,
    }


def test_maintenance_task_completion_rate_when_empty():
    response = client.get(
        "/analytics/maintenance-tasks/completion-rate"
    )

    assert response.status_code == 200
    assert response.json() == {
        "total_tasks": 0,
        "completed_tasks": 0,
        "completion_rate": 0.0,
    }

def test_overdue_maintenance_tasks():
    unit_id = create_test_unit()

    today = date.today()

    overdue_pending_id = create_test_task(
        unit_id,
        "Overdue pending task",
        assigned_to="Technician A",
        due_date=(today - timedelta(days=5)).isoformat(),
    )

    overdue_in_progress_id = create_test_task(
        unit_id,
        "Overdue in-progress task",
        assigned_to="Technician B",
        due_date=(today - timedelta(days=2)).isoformat(),
    )

    overdue_completed_id = create_test_task(
        unit_id,
        "Overdue completed task",
        due_date=(today - timedelta(days=10)).isoformat(),
    )

    create_test_task(
        unit_id,
        "Due today task",
        due_date=today.isoformat(),
    )

    update_task_status(overdue_in_progress_id, "in_progress")
    update_task_status(overdue_completed_id, "completed")

    response = client.get(
        "/analytics/maintenance-tasks/overdue"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0]["task_id"] == overdue_pending_id
    assert data[0]["title"] == "Overdue pending task"
    assert data[0]["assigned_to"] == "Technician A"
    assert data[0]["days_overdue"] == 5

    assert data[1]["task_id"] == overdue_in_progress_id
    assert data[1]["title"] == "Overdue in-progress task"
    assert data[1]["assigned_to"] == "Technician B"
    assert data[1]["days_overdue"] == 2

def test_maintenance_tasks_by_assignee():
    unit_id = create_test_unit()

    completed_id = create_test_task(
        unit_id,
        "Completed repair",
        assigned_to="Technician A",
    )

    create_test_task(
        unit_id,
        "Pending repair",
        assigned_to="Technician A",
    )

    in_progress_id = create_test_task(
        unit_id,
        "Technician B repair",
        assigned_to="Technician B",
    )

    create_test_task(
        unit_id,
        "Unassigned task",
    )

    update_task_status(completed_id, "completed")
    update_task_status(in_progress_id, "in_progress")

    response = client.get(
        "/analytics/maintenance-tasks/by-assignee"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 3

    assert data[0] == {
        "assigned_to": "Technician A",
        "total_tasks": 2,
        "pending_tasks": 1,
        "in_progress_tasks": 0,
        "completed_tasks": 1,
    }

    assert data[1] == {
        "assigned_to": "Technician B",
        "total_tasks": 1,
        "pending_tasks": 0,
        "in_progress_tasks": 1,
        "completed_tasks": 0,
    }

    assert data[2] == {
        "assigned_to": "Unassigned",
        "total_tasks": 1,
        "pending_tasks": 1,
        "in_progress_tasks": 0,
        "completed_tasks": 0,
    }

def test_maintenance_tasks_by_building():
    building_a_unit = create_test_unit(
        building_name="Building A",
        unit_number="101",
    )

    building_b_unit = create_test_unit(
        building_name="Building B",
        unit_number="201",
    )

    completed_id = create_test_task(
        building_a_unit,
        "Completed Building A task",
    )

    create_test_task(
        building_a_unit,
        "Pending Building A task",
    )

    in_progress_id = create_test_task(
        building_b_unit,
        "Building B task",
    )

    update_task_status(completed_id, "completed")
    update_task_status(in_progress_id, "in_progress")

    response = client.get(
        "/analytics/maintenance-tasks/by-building"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0] == {
        "building_name": "Building A",
        "total_tasks": 2,
        "pending_tasks": 1,
        "in_progress_tasks": 0,
        "completed_tasks": 1,
        "cancelled_tasks": 0,
    }

    assert data[1] == {
        "building_name": "Building B",
        "total_tasks": 1,
        "pending_tasks": 0,
        "in_progress_tasks": 1,
        "completed_tasks": 0,
        "cancelled_tasks": 0,
    }