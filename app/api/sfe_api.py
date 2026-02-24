from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_roles
from app.core.database import get_db
from app.models.entities import Allocation, Bill, Customer, CustomerOrder, InventoryLot, Item
from app.schemas.sfe import AllocateIn, BuildBillIn, CustomerIn, ItemIn, LotIn, OrderIn, StateActionIn
from app.services import sfe_service

router = APIRouter(prefix="/api", tags=["SFE"])


@router.post("/customers")
def create_customer(payload: CustomerIn, db: Session = Depends(get_db), _=Depends(require_roles('admin', 'super_admin'))):
    return sfe_service.create_customer(db, payload.name)


@router.get("/customers")
def list_customers(db: Session = Depends(get_db), _=Depends(require_roles('admin', 'super_admin'))):
    return db.query(Customer).order_by(Customer.id.desc()).all()


@router.post("/items")
def create_item(payload: ItemIn, db: Session = Depends(get_db), _=Depends(require_roles('admin', 'super_admin'))):
    return sfe_service.create_item(db, payload.model_dump())


@router.get("/items")
def list_items(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Item).order_by(Item.id.desc()).all()


@router.post("/orders")
def create_order(payload: OrderIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.role == 'customer' and user.customer_id != payload.customer_id:
        raise HTTPException(403, 'customer can only create own orders')
    return sfe_service.create_order(db, payload.customer_id, payload.item_id, payload.qty_requested)


@router.get("/orders")
def list_orders(db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(CustomerOrder)
    if user.role == 'customer':
        q = q.filter(CustomerOrder.customer_id == user.customer_id)
    return q.order_by(CustomerOrder.id.desc()).all()


@router.post("/lots")
def inbound_lot(payload: LotIn, db: Session = Depends(get_db), _=Depends(require_roles('admin', 'super_admin'))):
    return sfe_service.inbound_lot(db, payload.item_id, payload.qty_received, payload.location)


@router.get("/lots")
def list_lots(db: Session = Depends(get_db), _=Depends(require_roles('admin', 'super_admin'))):
    return db.query(InventoryLot).order_by(InventoryLot.id.desc()).all()


@router.post("/allocations/fifo")
def allocate_fifo(payload: AllocateIn, db: Session = Depends(get_db), _=Depends(require_roles('admin', 'super_admin'))):
    return sfe_service.allocate_fifo(db, payload.order_line_id, payload.allocated_by)


@router.get("/allocations")
def list_allocations(db: Session = Depends(get_db), _=Depends(require_roles('admin', 'super_admin'))):
    return db.query(Allocation).order_by(Allocation.id.desc()).all()


@router.post("/bills")
def build_bill(payload: BuildBillIn, db: Session = Depends(get_db), _=Depends(require_roles('admin', 'super_admin'))):
    return sfe_service.build_bill(db, payload.customer_id, payload.allocation_ids, payload.sale_unit_price)


@router.get("/bills")
def list_bills(db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(Bill)
    if user.role == 'customer':
        q = q.filter(Bill.customer_id == user.customer_id)
    return q.order_by(Bill.id.desc()).all()


@router.post("/bills/{bill_id}/state")
def bill_state_action(bill_id: int, payload: StateActionIn, db: Session = Depends(get_db), _=Depends(require_roles('admin', 'super_admin'))):
    return sfe_service.update_bill_state(db, bill_id, payload.action)


@router.post('/fifo/pending/{allocation_id}/resolve')
def resolve_fifo_pending(allocation_id: int, decision: StateActionIn, _=Depends(require_roles('super_admin'))):
    return {'allocation_id': allocation_id, 'decision': decision.action, 'status': 'resolved_by_super_admin'}
