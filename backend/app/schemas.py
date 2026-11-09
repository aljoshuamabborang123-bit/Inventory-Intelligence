from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import WorkOrderPriority, WorkOrderStatus


class PartCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    category: str = Field(min_length=1, max_length=100)
    quantity: int = Field(ge=0)


class PartUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    category: str = Field(min_length=1, max_length=100)
    quantity: int = Field(ge=0)


class PartResponse(BaseModel):
    id: int
    name: str
    category: str
    quantity: int

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

    model_config = ConfigDict(from_attributes=True)