from datetime import UTC, datetime

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import case, func, select, update
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Part,
    WorkOrder,
    WorkOrderPartUsage,
    WorkOrderPriority,
    WorkOrderStatus,
)
from app.schemas import (
    PartCreate,
    PartResponse,
    PartUpdate,
    WorkOrderCreate,
    WorkOrderPartUsageCreate,
    WorkOrderPartUsageResponse,
    WorkOrderResponse,
    WorkOrderUpdate,
)

app = FastAPI(title="Inventory Intelligence API", version="0.1.0")


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/parts", response_model=list[PartResponse], tags=["Parts"])
def get_parts(
    category: str | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[PartResponse]:

    statement = select(Part)

    if category:
        statement = statement.where(
            func.lower(Part.category) == category.lower()
        )

    statement = statement.limit(limit)

    return list(db.scalars(statement).all())


@app.post(
    "/parts",
    response_model=PartResponse,
    status_code=201,
    tags=["Parts"],
)
def create_part(
    part: PartCreate,
    db: Session = Depends(get_db),
) -> PartResponse:

    new_part = Part(**part.model_dump())

    db.add(new_part)
    db.commit()
    db.refresh(new_part)

    return new_part


@app.get(
    "/parts/{part_id}",
    response_model=PartResponse,
    tags=["Parts"],
)
def get_part(
    part_id: int,
    db: Session = Depends(get_db),
) -> PartResponse:

    part = db.get(Part, part_id)

    if part is None:
        raise HTTPException(
            status_code=404,
            detail="Part not found",
        )

    return part


@app.put(
    "/parts/{part_id}",
    response_model=PartResponse,
    tags=["Parts"],
)
def update_part(
    part_id: int,
    part: PartUpdate,
    db: Session = Depends(get_db),
) -> PartResponse:

    existing_part = db.get(Part, part_id)

    if existing_part is None:
        raise HTTPException(
            status_code=404,
            detail="Part not found",
        )

    for field, value in part.model_dump().items():
        setattr(existing_part, field, value)

    db.commit()
    db.refresh(existing_part)

    return existing_part


@app.delete(
    "/parts/{part_id}",
    status_code=204,
    tags=["Parts"],
)
def delete_part(
    part_id: int,
    db: Session = Depends(get_db),
) -> None:

    part = db.get(Part, part_id)

    if part is None:
        raise HTTPException(
            status_code=404,
            detail="Part not found",
        )

    db.delete(part)
    db.commit()

@app.get(
    "/work-orders",
    response_model=list[WorkOrderResponse],
    tags=["Work Orders"],
)
def get_work_orders(
    status: WorkOrderStatus | None = None,
    priority: WorkOrderPriority | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[WorkOrderResponse]:

    priority_order = case(
        (WorkOrder.priority == WorkOrderPriority.URGENT, 1),
        (WorkOrder.priority == WorkOrderPriority.HIGH, 2),
        (WorkOrder.priority == WorkOrderPriority.MEDIUM, 3),
        (WorkOrder.priority == WorkOrderPriority.LOW, 4),
    )

    statement = select(WorkOrder)

    if status is not None:
        statement = statement.where(WorkOrder.status == status)

    if priority is not None:
        statement = statement.where(WorkOrder.priority == priority)

    statement = (
        statement
        .order_by(priority_order, WorkOrder.created_at.desc())
        .limit(limit)
    )

    return list(db.scalars(statement).all())

@app.post(
    "/work-orders",
    response_model=WorkOrderResponse,
    status_code=201,
    tags=["Work Orders"],
)
def create_work_order(
    work_order: WorkOrderCreate,
    db: Session = Depends(get_db),
) -> WorkOrderResponse:

    new_work_order = WorkOrder(**work_order.model_dump())

    db.add(new_work_order)
    db.commit()
    db.refresh(new_work_order)

    return new_work_order

@app.get(
    "/work-orders/{work_order_id}",
    response_model=WorkOrderResponse,
    tags=["Work Orders"],
)
def get_work_order(
    work_order_id: int,
    db: Session = Depends(get_db),
) -> WorkOrderResponse:

    work_order = db.get(WorkOrder, work_order_id)

    if work_order is None:
        raise HTTPException(
            status_code=404,
            detail="Work order not found",
        )

    return work_order

@app.put(
    "/work-orders/{work_order_id}",
    response_model=WorkOrderResponse,
    tags=["Work Orders"],
)
def update_work_order(
    work_order_id: int,
    work_order: WorkOrderUpdate,
    db: Session = Depends(get_db),
) -> WorkOrderResponse:

    existing_work_order = db.get(WorkOrder, work_order_id)

    if existing_work_order is None:
        raise HTTPException(
            status_code=404,
            detail="Work order not found",
        )

    allowed_transitions = {
        WorkOrderStatus.OPEN: {
            WorkOrderStatus.IN_PROGRESS,
            WorkOrderStatus.CANCELLED,
        },
        WorkOrderStatus.IN_PROGRESS: {
            WorkOrderStatus.COMPLETED,
            WorkOrderStatus.CANCELLED,
        },
        WorkOrderStatus.COMPLETED: set(),
        WorkOrderStatus.CANCELLED: set(),
    }

    if work_order.status != existing_work_order.status:
        if work_order.status not in allowed_transitions[
            existing_work_order.status
        ]:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Cannot change status from "
                    f"{existing_work_order.status.value} "
                    f"to {work_order.status.value}"
                ),
            )

    for field, value in work_order.model_dump().items():
        setattr(existing_work_order, field, value)

    if (
        existing_work_order.status == WorkOrderStatus.COMPLETED
        and existing_work_order.completed_at is None
    ):
        existing_work_order.completed_at = datetime.now(UTC)

    db.commit()
    db.refresh(existing_work_order)

    return existing_work_order

@app.delete(
    "/work-orders/{work_order_id}",
    status_code=204,
    tags=["Work Orders"],
)
def delete_work_order(
    work_order_id: int,
    db: Session = Depends(get_db),
) -> None:

    work_order = db.get(WorkOrder, work_order_id)

    if work_order is None:
        raise HTTPException(
            status_code=404,
            detail="Work order not found",
        )

    db.delete(work_order)
    db.commit()

@app.post(
    "/work-orders/{work_order_id}/part-usage",
    response_model=WorkOrderPartUsageResponse,
    status_code=201,
    tags=["Work Order Part Usage"],
)
def record_part_usage(
    work_order_id: int,
    usage: WorkOrderPartUsageCreate,
    db: Session = Depends(get_db),
) -> WorkOrderPartUsageResponse:

    work_order = db.get(WorkOrder, work_order_id)

    if work_order is None:
        raise HTTPException(
            status_code=404,
            detail="Work order not found",
        )

    if work_order.status != WorkOrderStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=409,
            detail="Parts can only be consumed by work orders in progress",
        )

    part = db.get(Part, usage.part_id)

    if part is None:
        raise HTTPException(
            status_code=404,
            detail="Part not found",
        )

    try:
        stock_update = (
            update(Part)
            .where(
                Part.id == usage.part_id,
                Part.quantity >= usage.quantity_used,
            )
            .values(
                quantity=Part.quantity - usage.quantity_used,
            )
        )

        result = db.execute(stock_update)

        if result.rowcount != 1:
            raise HTTPException(
                status_code=409,
                detail="Insufficient stock",
            )

        new_usage = WorkOrderPartUsage(
            work_order_id=work_order_id,
            part_id=usage.part_id,
            quantity_used=usage.quantity_used,
        )

        db.add(new_usage)
        db.commit()
        db.refresh(new_usage)

    except Exception:
        db.rollback()
        raise

    return new_usage