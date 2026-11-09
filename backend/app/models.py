from datetime import UTC, date, datetime
from enum import Enum as PyEnum
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class WorkOrderStatus(PyEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class UnitStatus(PyEnum):
    OCCUPIED = "occupied"
    VACANT = "vacant"
    UNDER_MAINTENANCE = "under_maintenance"
    TURNOVER = "turnover"

class UnitTurnStatus(PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class WorkOrderPriority(PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

    @property
    def rank(self) -> int:
        return {
            WorkOrderPriority.LOW: 1,
            WorkOrderPriority.MEDIUM: 2,
            WorkOrderPriority.HIGH: 3,
            WorkOrderPriority.URGENT: 4,
        }[self]


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    unit_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[WorkOrderStatus] = mapped_column(
    SQLAlchemyEnum(
        WorkOrderStatus,
        name="work_order_status",
        native_enum=False,
        create_constraint=True,
        values_callable=lambda enum_cls: [
            member.value for member in enum_cls
        ],
    ),
    nullable=False,
    default=WorkOrderStatus.OPEN,
    )

    priority: Mapped[WorkOrderPriority] = mapped_column(
    SQLAlchemyEnum(
        WorkOrderPriority,
        name="work_order_priority",
        native_enum=False,
        create_constraint=True,
        values_callable=lambda enum_cls: [
            member.value for member in enum_cls
        ],
    ),
    nullable=False,
    default=WorkOrderPriority.MEDIUM,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    part_usages: Mapped[list["WorkOrderPartUsage"]] = relationship(
        "WorkOrderPartUsage",
        back_populates="work_order",
        passive_deletes="all",
    )

class Part(Base):
    __tablename__ = "parts"

    __table_args__ = (
        CheckConstraint(
            "quantity >= 0",
            name="check_part_quantity_nonnegative",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    part_usages: Mapped[list["WorkOrderPartUsage"]] = relationship(
        "WorkOrderPartUsage",
        back_populates="part",
        passive_deletes="all",
    )

class WorkOrderPartUsage(Base):
    __tablename__ = "work_order_part_usage"

    __table_args__ = (
        CheckConstraint(
            "quantity_used > 0",
            name="check_quantity_used_positive",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    work_order_id: Mapped[int] = mapped_column(
        ForeignKey("work_orders.id", ondelete="RESTRICT"),
        nullable=False,
    )

    part_id: Mapped[int] = mapped_column(
        ForeignKey("parts.id", ondelete="RESTRICT"),
        nullable=False,
    )

    quantity_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    @property
    def total_cost(self) -> Decimal:
        return self.quantity_used * self.unit_cost
    work_order: Mapped["WorkOrder"] = relationship(
        "WorkOrder",
        back_populates="part_usages",
    )

    part: Mapped["Part"] = relationship(
        "Part",
        back_populates="part_usages",
    )

class Unit(Base):
    __tablename__ = "units"
    __table_args__ = (
        UniqueConstraint(
            "building_name",
            "unit_number",
            name="uq_units_building_unit",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    building_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    unit_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    floor_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    status: Mapped[UnitStatus] = mapped_column(
        SQLAlchemyEnum(UnitStatus),
        nullable=False,
        default=UnitStatus.VACANT,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    turns: Mapped[list["UnitTurn"]] = relationship(
        back_populates="unit",
    )

class UnitTurn(Base):
    __tablename__ = "unit_turns"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    unit_id: Mapped[int] = mapped_column(
        ForeignKey("units.id", ondelete="RESTRICT"),
        nullable=False,
    )

    move_out_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[UnitTurnStatus] = mapped_column(
        SQLAlchemyEnum(UnitTurnStatus),
        nullable=False,
        default=UnitTurnStatus.PENDING,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    unit: Mapped["Unit"] = relationship(
        back_populates="turns",
    )