from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models import (
    MaintenanceTaskCategory,
    MaintenanceTaskStatus,
    UnitStatus,
    UnitTurnStatus,
    WorkOrderPriority,
    WorkOrderStatus,
)

class PartCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    category: str = Field(min_length=1, max_length=100)
    quantity: int = Field(ge=0)
    unit_cost: Decimal = Field(default=Decimal("0.00"), ge=0)

class PartUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    category: str = Field(min_length=1, max_length=100)
    quantity: int = Field(ge=0)
    unit_cost: Decimal | None = Field(default=None, ge=0)


class PartResponse(BaseModel):
    id: int
    name: str
    category: str
    quantity: int
    unit_cost: Decimal

    model_config = ConfigDict(from_attributes=True)

class WorkOrderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str
    unit_number: str = Field(min_length=1, max_length=50)
    priority: WorkOrderPriority = WorkOrderPriority.MEDIUM


class WorkOrderUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str
    unit_number: str = Field(min_length=1, max_length=50)
    status: WorkOrderStatus
    priority: WorkOrderPriority


class WorkOrderResponse(BaseModel):
    id: int
    title: str
    description: str
    unit_number: str
    status: WorkOrderStatus
    priority: WorkOrderPriority
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

class WorkOrderPartUsageCreate(BaseModel):
    part_id: int = Field(gt=0)
    quantity_used: int = Field(gt=0)


class WorkOrderPartUsageResponse(BaseModel):
    id: int
    work_order_id: int
    part_id: int
    quantity_used: int
    recorded_at: datetime
    unit_cost: Decimal
    total_cost: Decimal

    model_config = ConfigDict(from_attributes=True)

class PartCategoryConsumptionResponse(BaseModel):
    category: str
    total_quantity_used: int

class PartsConsumptionSummaryResponse(BaseModel):
    total_quantity_consumed: int
    unique_parts_count: int
    work_orders_with_usage_count: int
    consumption_by_category: list[PartCategoryConsumptionResponse]

class MostUsedPartResponse(BaseModel):
    part_id: int
    part_name: str
    category: str
    total_quantity_used: int

class LowStockPartResponse(BaseModel):
    part_id: int
    part_name: str
    category: str
    current_quantity: int
    threshold: int

class MaintenanceCostSummaryResponse(BaseModel):
    total_parts_cost: Decimal
    total_usage_records: int
    work_orders_with_cost_count: int

class WorkOrderCostResponse(BaseModel):
    work_order_id: int
    work_order_title: str
    unit_number: str
    total_parts_cost: Decimal

class CategoryCostResponse(BaseModel):
    category: str
    total_parts_cost: Decimal

class UnitCreate(BaseModel):
    building_name: str = Field(min_length=1, max_length=100)
    unit_number: str = Field(min_length=1, max_length=50)
    floor_number: int | None = None
    status: UnitStatus = UnitStatus.VACANT


class UnitUpdate(BaseModel):
    building_name: str = Field(min_length=1, max_length=100)
    unit_number: str = Field(min_length=1, max_length=50)
    floor_number: int | None = None
    status: UnitStatus


class UnitResponse(BaseModel):
    id: int
    building_name: str
    unit_number: str
    floor_number: int | None
    status: UnitStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UnitTurnCreate(BaseModel):
    unit_id: int = Field(gt=0)
    move_out_date: date
    notes: str | None = None


class UnitTurnUpdate(BaseModel):
    move_out_date: date
    status: UnitTurnStatus
    notes: str | None = None


class UnitTurnResponse(BaseModel):
    id: int
    unit_id: int
    move_out_date: date
    status: UnitTurnStatus
    started_at: datetime | None
    completed_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MaintenanceTaskCreate(BaseModel):
    unit_id: int = Field(gt=0)
    unit_turn_id: int | None = Field(default=None, gt=0)
    work_order_id: int | None = Field(default=None, gt=0)

    title: str = Field(min_length=1, max_length=200)
    description: str

    category: MaintenanceTaskCategory = MaintenanceTaskCategory.OTHER
    priority: WorkOrderPriority = WorkOrderPriority.MEDIUM

    assigned_to: str | None = Field(default=None, max_length=150)
    due_date: date | None = None

class MaintenanceTaskUpdate(BaseModel):
    unit_turn_id: int | None = Field(default=None, gt=0)
    work_order_id: int | None = Field(default=None, gt=0)

    title: str = Field(min_length=1, max_length=200)
    description: str

    category: MaintenanceTaskCategory
    status: MaintenanceTaskStatus
    priority: WorkOrderPriority

    assigned_to: str | None = Field(default=None, max_length=150)
    due_date: date | None = None

class MaintenanceTaskResponse(BaseModel):
    id: int
    unit_id: int
    unit_turn_id: int | None
    work_order_id: int | None

    title: str
    description: str

    category: MaintenanceTaskCategory
    status: MaintenanceTaskStatus
    priority: WorkOrderPriority

    assigned_to: str | None
    due_date: date | None
    completed_at: datetime | None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MaintenanceTaskSummaryResponse(BaseModel):
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    cancelled_tasks: int

class MaintenanceTaskCompletionRateResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    completion_rate: float

class OverdueMaintenanceTaskResponse(BaseModel):
    task_id: int
    title: str
    unit_id: int
    building_name: str
    unit_number: str
    assigned_to: str | None
    priority: WorkOrderPriority
    due_date: date
    days_overdue: int

class MaintenanceTaskAssigneeAnalyticsResponse(BaseModel):
    assigned_to: str
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int

class MaintenanceTaskBuildingAnalyticsResponse(BaseModel):
    building_name: str
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    cancelled_tasks: int

class DashboardInventoryResponse(BaseModel):
    total_parts: int
    total_stock_quantity: int
    total_inventory_value: Decimal
    low_stock_count: int
    out_of_stock_count: int
    low_stock_threshold: int


class DashboardUnitsResponse(BaseModel):
    total_units: int
    occupied_units: int
    vacant_units: int
    under_maintenance_units: int
    turnover_units: int
    occupancy_rate: float


class DashboardWorkOrdersResponse(BaseModel):
    total_work_orders: int
    open_work_orders: int
    in_progress_work_orders: int
    completed_work_orders: int
    cancelled_work_orders: int
    high_priority_work_orders: int
    urgent_priority_work_orders: int


class DashboardMaintenanceTasksResponse(BaseModel):
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    cancelled_tasks: int
    overdue_tasks: int
    unassigned_tasks: int
    high_priority_tasks: int
    urgent_priority_tasks: int


class DashboardCostsResponse(BaseModel):
    total_parts_cost: Decimal
    total_usage_records: int
    work_orders_with_cost_count: int


class DashboardSummaryResponse(BaseModel):
    inventory: DashboardInventoryResponse
    units: DashboardUnitsResponse
    work_orders: DashboardWorkOrdersResponse
    maintenance_tasks: DashboardMaintenanceTasksResponse
    costs: DashboardCostsResponse