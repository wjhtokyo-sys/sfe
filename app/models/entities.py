from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TimestampMixin:
    # 与本地系统时间同步（避免UTC偏移导致的日期/时间显示错位）
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


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
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


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
    currency: Mapped[str] = mapped_column(String(8), default="JPY")
    payment_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


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


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(32), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), nullable=True)


class AuthToken(Base, TimestampMixin):
    __tablename__ = "auth_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)


class Supplier(Base, TimestampMixin):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    supplier_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class PurchaseOrder(Base, TimestampMixin):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    po_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), index=True)
    payment_status: Mapped[str] = mapped_column(String(16), default="unpaid")
    status: Mapped[str] = mapped_column(String(32), default="created_unchecked")
    total_cost: Mapped[float] = mapped_column(Float, default=0)
    purchased_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PurchaseOrderLine(Base, TimestampMixin):
    __tablename__ = "purchase_order_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), index=True)
    jan: Mapped[str] = mapped_column(String(64), index=True)
    item_name_snapshot: Mapped[str] = mapped_column(String(255))
    qty: Mapped[int] = mapped_column(Integer)
    unit_cost: Mapped[float] = mapped_column(Float)
    line_total: Mapped[float] = mapped_column(Float)


class FifoPendingTask(Base, TimestampMixin):
    __tablename__ = "fifo_pending_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    purchase_order_line_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_order_lines.id"), nullable=True, index=True)
    source_po_no: Mapped[str] = mapped_column(String(64), index=True)
    jan: Mapped[str] = mapped_column(String(64), index=True)
    item_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    qty: Mapped[int] = mapped_column(Integer, default=0)
    reason_code: Mapped[str] = mapped_column(String(64))
    reason_text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
