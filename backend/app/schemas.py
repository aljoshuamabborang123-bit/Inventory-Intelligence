from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models import (
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