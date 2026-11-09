from datetime import UTC, datetime

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import case, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database import get_db

from app.models import (
    Part,
    Unit,
    UnitStatus,
    WorkOrder,
    WorkOrderPartUsage,
    WorkOrderPriority,
    WorkOrderStatus,
)

from app.schemas import (
    UnitCreate,
    UnitResponse,
    UnitUpdate,
    MaintenanceCostSummaryResponse,
    CategoryCostResponse,
    WorkOrderCostResponse,
    LowStockPartResponse,
    MostUsedPartResponse,
    PartCreate,
    PartResponse,
    PartUpdate,
    WorkOrderCreate,
    WorkOrderPartUsageCreate,
    WorkOrderPartUsageResponse,
    WorkOrderResponse,
    WorkOrderUpdate,
    PartCategoryConsumptionResponse,
    PartsConsumptionSummaryResponse,
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

    for field, value in part.model_dump(exclude_none=True).items():
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

    try:
        db.delete(part)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Cannot delete part because it has recorded usage history",
        )

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

    try:
        db.delete(work_order)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Cannot delete work order because it has recorded parts usage",
        )

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
            unit_cost=part.unit_cost,
        )

        db.add(new_usage)
        db.commit()
        db.refresh(new_usage)

    except Exception:
        db.rollback()
        raise

    return new_usage

@app.get(
    "/work-orders/{work_order_id}/part-usage",
    response_model=list[WorkOrderPartUsageResponse],
    tags=["Work Order Part Usage"],
)
def get_work_order_part_usage(
    work_order_id: int,
    db: Session = Depends(get_db),
) -> list[WorkOrderPartUsageResponse]:

    work_order = db.get(WorkOrder, work_order_id)

    if work_order is None:
        raise HTTPException(
            status_code=404,
            detail="Work order not found",
        )

    statement = (
        select(WorkOrderPartUsage)
        .where(
            WorkOrderPartUsage.work_order_id == work_order_id
        )
        .order_by(
            WorkOrderPartUsage.recorded_at.asc(),
            WorkOrderPartUsage.id.asc(),
        )
    )

    usages = db.scalars(statement).all()

    return list(usages)

@app.get(
    "/analytics/parts-consumption",
    response_model=PartsConsumptionSummaryResponse,
    tags=["Analytics"],
)
def get_parts_consumption_summary(
    db: Session = Depends(get_db),
) -> PartsConsumptionSummaryResponse:

    totals_statement = select(
        func.coalesce(
            func.sum(WorkOrderPartUsage.quantity_used),
            0,
        ).label("total_quantity_consumed"),
        func.count(
            func.distinct(WorkOrderPartUsage.part_id)
        ).label("unique_parts_count"),
        func.count(
            func.distinct(WorkOrderPartUsage.work_order_id)
        ).label("work_orders_with_usage_count"),
    )

    totals = db.execute(totals_statement).one()

    category_statement = (
        select(
            Part.category,
            func.sum(
                WorkOrderPartUsage.quantity_used
            ).label("total_quantity_used"),
        )
        .join(
            WorkOrderPartUsage,
            WorkOrderPartUsage.part_id == Part.id,
        )
        .group_by(Part.category)
        .order_by(Part.category.asc())
    )

    category_rows = db.execute(category_statement).all()

    return PartsConsumptionSummaryResponse(
        total_quantity_consumed=totals.total_quantity_consumed,
        unique_parts_count=totals.unique_parts_count,
        work_orders_with_usage_count=totals.work_orders_with_usage_count,
        consumption_by_category=[
            PartCategoryConsumptionResponse(
                category=row.category,
                total_quantity_used=row.total_quantity_used,
            )
            for row in category_rows
        ],
    )

@app.get(
    "/analytics/maintenance-costs",
    response_model=MaintenanceCostSummaryResponse,
    tags=["Analytics"],
)

def get_maintenance_cost_summary(
    db: Session = Depends(get_db),
) -> MaintenanceCostSummaryResponse:

    statement = select(
        func.coalesce(
            func.sum(
                WorkOrderPartUsage.quantity_used
                * WorkOrderPartUsage.unit_cost
            ),
            0,
        ).label("total_parts_cost"),
        func.count(
            WorkOrderPartUsage.id
        ).label("total_usage_records"),
        func.count(
            func.distinct(WorkOrderPartUsage.work_order_id)
        ).label("work_orders_with_cost_count"),
    )

    totals = db.execute(statement).one()

    return MaintenanceCostSummaryResponse(
        total_parts_cost=totals.total_parts_cost,
        total_usage_records=totals.total_usage_records,
        work_orders_with_cost_count=totals.work_orders_with_cost_count,
    )

@app.get(
    "/analytics/maintenance-costs/by-work-order",
    response_model=list[WorkOrderCostResponse],
    tags=["Analytics"],
)
def get_maintenance_costs_by_work_order(
    db: Session = Depends(get_db),
) -> list[WorkOrderCostResponse]:

    statement = (
        select(
            WorkOrder.id.label("work_order_id"),
            WorkOrder.title.label("work_order_title"),
            WorkOrder.unit_number,
            func.sum(
                WorkOrderPartUsage.quantity_used
                * WorkOrderPartUsage.unit_cost
            ).label("total_parts_cost"),
        )
        .join(
            WorkOrderPartUsage,
            WorkOrderPartUsage.work_order_id == WorkOrder.id,
        )
        .group_by(
            WorkOrder.id,
            WorkOrder.title,
            WorkOrder.unit_number,
        )
        .order_by(
            func.sum(
                WorkOrderPartUsage.quantity_used
                * WorkOrderPartUsage.unit_cost
            ).desc(),
            WorkOrder.id.asc(),
        )
    )

    rows = db.execute(statement).all()

    return [
        WorkOrderCostResponse(
            work_order_id=row.work_order_id,
            work_order_title=row.work_order_title,
            unit_number=row.unit_number,
            total_parts_cost=row.total_parts_cost,
        )
        for row in rows
    ]

@app.get(
    "/analytics/maintenance-costs/by-category",
    response_model=list[CategoryCostResponse],
    tags=["Analytics"],
)
def get_maintenance_costs_by_category(
    db: Session = Depends(get_db),
) -> list[CategoryCostResponse]:

    statement = (
        select(
            Part.category,
            func.sum(
                WorkOrderPartUsage.quantity_used
                * WorkOrderPartUsage.unit_cost
            ).label("total_parts_cost"),
        )
        .join(
            WorkOrderPartUsage,
            WorkOrderPartUsage.part_id == Part.id,
        )
        .group_by(Part.category)
        .order_by(
            func.sum(
                WorkOrderPartUsage.quantity_used
                * WorkOrderPartUsage.unit_cost
            ).desc(),
            Part.category.asc(),
        )
    )

    rows = db.execute(statement).all()

    return [
        CategoryCostResponse(
            category=row.category,
            total_parts_cost=row.total_parts_cost,
        )
        for row in rows
    ]

@app.get(
    "/analytics/most-used-parts",
    response_model=list[MostUsedPartResponse],
    tags=["Analytics"],
)
def get_most_used_parts(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[MostUsedPartResponse]:

    statement = (
        select(
            Part.id.label("part_id"),
            Part.name.label("part_name"),
            Part.category,
            func.sum(
                WorkOrderPartUsage.quantity_used
            ).label("total_quantity_used"),
        )
        .join(
            WorkOrderPartUsage,
            WorkOrderPartUsage.part_id == Part.id,
        )
        .group_by(
            Part.id,
            Part.name,
            Part.category,
        )
        .order_by(
            func.sum(
                WorkOrderPartUsage.quantity_used
            ).desc(),
            Part.id.asc(),
        )
        .limit(limit)
    )

    rows = db.execute(statement).all()

    return [
        MostUsedPartResponse(
            part_id=row.part_id,
            part_name=row.part_name,
            category=row.category,
            total_quantity_used=row.total_quantity_used,
        )
        for row in rows
    ]

@app.get(
    "/analytics/low-stock",
    response_model=list[LowStockPartResponse],
    tags=["Analytics"],
)
def get_low_stock_parts(
    threshold: int = Query(default=10, ge=0),
    db: Session = Depends(get_db),
) -> list[LowStockPartResponse]:

    statement = (
        select(Part)
        .where(Part.quantity <= threshold)
        .order_by(
            Part.quantity.asc(),
            Part.name.asc(),
        )
    )

    parts = db.scalars(statement).all()

    return [
        LowStockPartResponse(
            part_id=part.id,
            part_name=part.name,
            category=part.category,
            current_quantity=part.quantity,
            threshold=threshold,
        )
        for part in parts
    ]

@app.post(
    "/units",
    response_model=UnitResponse,
    status_code=201,
    tags=["Units"],
)
def create_unit(
    unit_data: UnitCreate,
    db: Session = Depends(get_db),
) -> UnitResponse:

    unit = Unit(**unit_data.model_dump())

    db.add(unit)

    try:
        db.commit()
        db.refresh(unit)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A unit with this building name and unit number already exists.",
        )

    return unit

@app.get(
    "/units",
    response_model=list[UnitResponse],
    tags=["Units"],
)
def get_units(
    building_name: str | None = None,
    status: UnitStatus | None = None,
    floor_number: int | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[UnitResponse]:

    statement = select(Unit)

    if building_name:
        statement = statement.where(
            func.lower(Unit.building_name) == building_name.lower()
        )

    if status:
        statement = statement.where(Unit.status == status)

    if floor_number is not None:
        statement = statement.where(
            Unit.floor_number == floor_number
        )

    statement = (
        statement
        .order_by(Unit.building_name, Unit.unit_number)
        .limit(limit)
    )

    return db.scalars(statement).all()

@app.get(
    "/units/{unit_id}",
    response_model=UnitResponse,
    tags=["Units"],
)
def get_unit(
    unit_id: int,
    db: Session = Depends(get_db),
) -> UnitResponse:

    unit = db.get(Unit, unit_id)

    if unit is None:
        raise HTTPException(
            status_code=404,
            detail="Unit not found.",
        )

    return unit

@app.put(
    "/units/{unit_id}",
    response_model=UnitResponse,
    tags=["Units"],
)
def update_unit(
    unit_id: int,
    unit_data: UnitUpdate,
    db: Session = Depends(get_db),
) -> UnitResponse:

    unit = db.get(Unit, unit_id)

    if unit is None:
        raise HTTPException(
            status_code=404,
            detail="Unit not found.",
        )

    for field, value in unit_data.model_dump().items():
        setattr(unit, field, value)

    try:
        db.commit()
        db.refresh(unit)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A unit with this building name and unit number already exists.",
        )

    return unit