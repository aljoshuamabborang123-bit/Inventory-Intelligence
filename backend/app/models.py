from datetime import UTC, datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class WorkOrderStatus(PyEnum):
    OPEN = "open"
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

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    work_order: Mapped["WorkOrder"] = relationship(
        "WorkOrder",
        back_populates="part_usages",
    )

    part: Mapped["Part"] = relationship(
        "Part",
        back_populates="part_usages",
    )