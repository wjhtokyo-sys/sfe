from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Item(Base, TimestampMixin):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    jan: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    brand: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(255))
    spec: Mapped[str | None] = mapped_column(String(255), nullable=True)
    msrp_price: Mapped[float] = mapped_column(Float, default=0)
    in_qty: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128))


class CustomerOrder(Base, TimestampMixin):
    __tablename__ = "customer_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    jan_snapshot: Mapped[str] = mapped_column(String(64))
    item_name_snapshot: Mapped[str] = mapped_column(String(255))
    qty_requested: Mapped[int] = mapped_column(Integer)
    qty_allocated: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="open")


class InventoryLot(Base, TimestampMixin):
    __tablename__ = "inventory_lots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    qty_received: Mapped[int] = mapped_column(Integer)
    qty_remaining: Mapped[int] = mapped_column(Integer)
    fifo_rank: Mapped[int] = mapped_column(Integer, index=True)
    location: Mapped[str | None] = mapped_column(String(128), nullable=True)


class Allocation(Base, TimestampMixin):
    __tablename__ = "allocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    order_line_id: Mapped[int] = mapped_column(ForeignKey("customer_orders.id"), index=True)
    lot_id: Mapped[int] = mapped_column(ForeignKey("inventory_lots.id"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    qty_allocated: Mapped[int] = mapped_column(Integer)
    fifo_rank_snapshot: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="active")
    allocated_by: Mapped[str] = mapped_column(String(64), default="system")


class Bill(Base, TimestampMixin):
    __tablename__ = "bills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    bill_no: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(16), default="draft")
    payment_status: Mapped[str] = mapped_column(String(16), default="unpaid")
    shipping_status: Mapped[str] = mapped_column(String(16), default="not_shipped")
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    currency: Mapped[str] = mapped_column(String(8), default="CNY")
    payment_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class BillLine(Base, TimestampMixin):
    __tablename__ = "bill_lines"
    __table_args__ = (UniqueConstraint("bill_id", "allocation_id", name="uq_bill_allocation"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bill_id: Mapped[int] = mapped_column(ForeignKey("bills.id"), index=True)
    allocation_id: Mapped[int] = mapped_column(ForeignKey("allocations.id"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    jan_snapshot: Mapped[str] = mapped_column(String(64))
    item_name_snapshot: Mapped[str] = mapped_column(String(255))
    qty: Mapped[int] = mapped_column(Integer)
    sale_unit_price: Mapped[float] = mapped_column(Float)
    line_amount: Mapped[float] = mapped_column(Float)
