from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.entities import Allocation, Bill, BillLine, Customer, CustomerOrder, InventoryLot, Item

BILL_TRANSITIONS = {
    "status": {"draft": ["issued"], "issued": ["archived"], "archived": []},
    "payment_status": {"unpaid": ["paid"], "paid": ["received"], "received": []},
    "shipping_status": {"not_shipped": ["shipped"], "shipped": ["delivered"], "delivered": []},
}

BILL_STAGE_FLOW = ["created", "paid", "confirmed", "shipped", "received", "archived"]
BILL_STAGE_LABEL = {
    "created": "已创建",
    "paid": "已支付",
    "confirmed": "已确认支付",
    "shipped": "已发货",
    "received": "已收货",
    "archived": "已归档",
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

    bill_no = f"B{datetime.now().strftime('%Y%m%d%H%M%S')}"
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


def get_bill_stage(bill: Bill) -> str:
    if bill.status == 'archived':
        return 'archived'
    if bill.shipping_status == "delivered":
        return "received"
    if bill.shipping_status == "shipped":
        return "shipped"
    if bill.payment_status == "received":
        return "confirmed"
    if bill.payment_status == "paid":
        return "paid"
    return "created"


def set_bill_stage(bill: Bill, stage: str):
    if stage not in BILL_STAGE_FLOW:
        raise HTTPException(400, "unsupported stage")

    if stage == "created":
        bill.status = "issued"
        bill.payment_status = "unpaid"
        bill.shipping_status = "not_shipped"
    elif stage == "paid":
        bill.status = "issued"
        bill.payment_status = "paid"
        bill.shipping_status = "not_shipped"
    elif stage == "confirmed":
        bill.status = "issued"
        bill.payment_status = "received"
        bill.payment_confirmed_at = datetime.now()
        bill.shipping_status = "not_shipped"
    elif stage == "shipped":
        bill.status = "issued"
        bill.payment_status = "received"
        bill.payment_confirmed_at = bill.payment_confirmed_at or datetime.now()
        bill.shipping_status = "shipped"
    elif stage == "received":
        bill.status = "issued"
        bill.payment_status = "received"
        bill.payment_confirmed_at = bill.payment_confirmed_at or datetime.now()
        bill.shipping_status = "delivered"
    elif stage == "archived":
        bill.status = 'archived'
        bill.payment_status = 'received'
        bill.shipping_status = 'delivered'
        bill.archived_at = datetime.now()


def update_bill_state(db: Session, bill_id: int, action: str, actor_role: str):
    bill = db.get(Bill, bill_id)
    if not bill:
        raise HTTPException(404, "bill not found")

    action_to_stage = {
        "pay": "paid",
        "confirm_receipt": "confirmed",
        "ship": "shipped",
        "deliver": "received",
        "archive": "archived",
        "created": "created",
    }
    if action not in action_to_stage:
        raise HTTPException(400, "unsupported action")

    target_stage = action_to_stage[action]
    current_stage = get_bill_stage(bill)
    current_idx = BILL_STAGE_FLOW.index(current_stage)
    target_idx = BILL_STAGE_FLOW.index(target_stage)

    if actor_role == 'customer':
        allowed = ((current_stage == 'created' and target_stage == 'paid') or (current_stage == 'shipped' and target_stage == 'received'))
        if not allowed:
            raise HTTPException(403, '没有权限')
    elif actor_role == 'super_admin':
        if target_idx < current_idx:
            raise HTTPException(400, '状态流不可逆')
    else:
        if target_idx != current_idx + 1:
            raise HTTPException(400, '状态流不可逆')

    set_bill_stage(bill, target_stage)
    db.commit()
    db.refresh(bill)
    return bill


def search_items(db: Session, keyword: str | None):
    q = db.query(Item)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(or_(Item.jan.like(kw), Item.name.like(kw), Item.brand.like(kw)))
    return q.order_by(Item.id.desc()).all()


def build_bill_from_orders(db: Session, order_ids: list[int], allocated_by: str, sale_unit_price: float):
    if not order_ids:
        raise HTTPException(400, "请选择订单")
    orders = db.query(CustomerOrder).filter(CustomerOrder.id.in_(order_ids)).all()
    if len(orders) != len(order_ids):
        raise HTTPException(400, "订单不存在")
    customer_ids = {o.customer_id for o in orders}
    if len(customer_ids) != 1:
        raise HTTPException(400, "仅允许同一客户订单合并账单")

    for o in orders:
        if o.status != 'closed':
            allocate_fifo(db, o.id, allocated_by)

    allocs = db.query(Allocation).filter(Allocation.order_line_id.in_(order_ids), Allocation.status == 'active').all()
    return build_bill(db, orders[0].customer_id, [a.id for a in allocs], sale_unit_price)
