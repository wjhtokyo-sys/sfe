from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.entities import Allocation, Bill, BillLine, Customer, CustomerOrder, InventoryLot, Item

BILL_TRANSITIONS = {
    "status": {"draft": ["issued"], "issued": ["archived"], "archived": []},
    "payment_status": {"unpaid": ["paid"], "paid": ["received"], "received": []},
    "shipping_status": {"not_shipped": ["shipped"], "shipped": ["delivered"], "delivered": []},
}


def create_customer(db: Session, name: str):
    obj = Customer(name=name)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_item(db: Session, payload: dict):
    obj = Item(**payload)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_order(db: Session, customer_id: int, item_id: int, qty_requested: int):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "item not found")
    if qty_requested <= 0:
        raise HTTPException(400, "qty_requested must > 0")
    obj = CustomerOrder(
        customer_id=customer_id,
        item_id=item_id,
        jan_snapshot=item.jan,
        item_name_snapshot=item.name,
        qty_requested=qty_requested,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def inbound_lot(db: Session, item_id: int, qty_received: int, location: str | None):
    if qty_received <= 0:
        raise HTTPException(400, "qty_received must > 0")
    max_rank = db.query(InventoryLot).filter(InventoryLot.item_id == item_id).count()
    obj = InventoryLot(
        item_id=item_id,
        qty_received=qty_received,
        qty_remaining=qty_received,
        fifo_rank=max_rank + 1,
        location=location,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def allocate_fifo(db: Session, order_line_id: int, allocated_by: str):
    order = db.get(CustomerOrder, order_line_id)
    if not order:
        raise HTTPException(404, "order not found")

    need = order.qty_requested - order.qty_allocated
    if need <= 0:
        raise HTTPException(400, "order already fulfilled")

    lots = (
        db.query(InventoryLot)
        .filter(InventoryLot.item_id == order.item_id, InventoryLot.qty_remaining > 0)
        .order_by(InventoryLot.fifo_rank.asc())
        .all()
    )
    if not lots:
        raise HTTPException(400, "no stock available")

    created = []
    for lot in lots:
        if need <= 0:
            break
        take = min(need, lot.qty_remaining)
        lot.qty_remaining -= take
        alloc = Allocation(
            customer_id=order.customer_id,
            order_line_id=order.id,
            lot_id=lot.id,
            item_id=order.item_id,
            qty_allocated=take,
            fifo_rank_snapshot=lot.fifo_rank,
            status="active",
            allocated_by=allocated_by,
        )
        db.add(alloc)
        created.append(alloc)
        need -= take
        order.qty_allocated += take

    order.status = "closed" if order.qty_allocated >= order.qty_requested else "open"
    db.commit()
    return [
        {
            "id": a.id,
            "customer_id": a.customer_id,
            "order_line_id": a.order_line_id,
            "lot_id": a.lot_id,
            "item_id": a.item_id,
            "qty_allocated": a.qty_allocated,
            "fifo_rank_snapshot": a.fifo_rank_snapshot,
            "status": a.status,
            "allocated_by": a.allocated_by,
            "created_at": a.created_at,
        }
        for a in created
    ]


def build_bill(db: Session, customer_id: int, allocation_ids: list[int], sale_unit_price: float):
    if sale_unit_price <= 0:
        raise HTTPException(400, "sale_unit_price must > 0")

    allocations = (
        db.query(Allocation)
        .filter(Allocation.id.in_(allocation_ids), Allocation.customer_id == customer_id)
        .all()
    )
    if len(allocations) != len(allocation_ids):
        raise HTTPException(400, "some allocations not found")

    for a in allocations:
        if a.status != "active":
            raise HTTPException(400, f"allocation {a.id} is not active")

    bill_no = f"B{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    bill = Bill(customer_id=customer_id, bill_no=bill_no, status="issued")
    db.add(bill)
    db.flush()

    total = 0.0
    for a in allocations:
        order = db.get(CustomerOrder, a.order_line_id)
        line_amount = a.qty_allocated * sale_unit_price
        total += line_amount
        line = BillLine(
            bill_id=bill.id,
            allocation_id=a.id,
            item_id=a.item_id,
            jan_snapshot=order.jan_snapshot,
            item_name_snapshot=order.item_name_snapshot,
            qty=a.qty_allocated,
            sale_unit_price=sale_unit_price,
            line_amount=line_amount,
        )
        a.status = "billed"
        db.add(line)

    bill.total_amount = total
    db.commit()
    db.refresh(bill)
    return bill


def update_bill_state(db: Session, bill_id: int, action: str):
    bill = db.get(Bill, bill_id)
    if not bill:
        raise HTTPException(404, "bill not found")

    mapping = {
        "issue": ("status", "issued"),
        "archive": ("status", "archived"),
        "pay": ("payment_status", "paid"),
        "confirm_receipt": ("payment_status", "received"),
        "ship": ("shipping_status", "shipped"),
        "deliver": ("shipping_status", "delivered"),
    }
    if action not in mapping:
        raise HTTPException(400, "unsupported action")

    field, target = mapping[action]
    current = getattr(bill, field)
    if target not in BILL_TRANSITIONS[field][current]:
        raise HTTPException(400, f"state guard blocked: {field} {current} -> {target}")

    setattr(bill, field, target)
    if action == "confirm_receipt":
        bill.payment_confirmed_at = datetime.utcnow()
    db.commit()
    db.refresh(bill)
    return bill
