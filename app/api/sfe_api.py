from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from openpyxl import Workbook, load_workbook
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_roles
from app.core.database import get_db
from app.models.entities import Allocation, Bill, Customer, CustomerOrder, InventoryLot, Item, User
from app.schemas.sfe import AllocateIn, BuildBillIn, CustomerIn, ItemIn, LotIn, OrderIn, StateActionIn
from app.services import sfe_service

router = APIRouter(prefix="/api", tags=["SFE"])


@router.post("/customers")
def create_customer(payload: CustomerIn, db: Session = Depends(get_db), _=Depends(require_roles('admin', 'super_admin'))):
    return sfe_service.create_customer(db, payload.name)


@router.get("/customers")
def list_customers(db: Session = Depends(get_db), _=Depends(require_roles('admin', 'super_admin'))):
    return db.query(Customer).order_by(Customer.id.desc()).all()


@router.post('/super/customers')
def super_create_customer_user(payload: dict, db: Session = Depends(get_db), _=Depends(require_roles('super_admin'))):
    username = str(payload.get('username', '')).strip()
    password = str(payload.get('password', '')).strip()
    customer_name = str(payload.get('customer_name', '')).strip()
    if not username or not password or not customer_name:
        raise HTTPException(400, '请填写完整客户账号信息')
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(400, '用户名已存在')
    c = Customer(name=customer_name, is_active=True)
    db.add(c)
    db.flush()
    u = User(username=username, password=password, role='customer', customer_id=c.id, is_active=True)
    db.add(u)
    db.commit()
    return {'ok': True}


@router.get('/super/customers')
def super_customer_users(db: Session = Depends(get_db), _=Depends(require_roles('super_admin'))):
    users = db.query(User).filter(User.role == 'customer').order_by(User.id.desc()).all()
    out = []
    for u in users:
        c = db.get(Customer, u.customer_id) if u.customer_id else None
        out.append({
            'user_id': u.id,
            'username': u.username,
            'is_active': u.is_active,
            'customer_id': u.customer_id,
            'customer_name': c.name if c else None,
            'customer_active': c.is_active if c else None,
        })
    return out


@router.patch('/super/customers/{user_id}')
def super_update_customer_user(user_id: int, payload: dict, db: Session = Depends(get_db), _=Depends(require_roles('super_admin'))):
    u = db.get(User, user_id)
    if not u or u.role != 'customer':
        raise HTTPException(404, '客户用户不存在')
    if 'password' in payload and payload['password']:
        u.password = payload['password']
    if 'is_active' in payload:
        u.is_active = bool(payload['is_active'])
    if u.customer_id:
        c = db.get(Customer, u.customer_id)
        if c and 'is_active' in payload:
            c.is_active = bool(payload['is_active'])
        if c and payload.get('customer_name'):
            c.name = payload['customer_name']
    db.commit()
    return {'ok': True}


@router.delete('/super/customers/{user_id}')
def super_delete_customer_user(user_id: int, db: Session = Depends(get_db), _=Depends(require_roles('super_admin'))):
    u = db.get(User, user_id)
    if not u or u.role != 'customer':
        raise HTTPException(404, '客户用户不存在')
    c = db.get(Customer, u.customer_id) if u.customer_id else None
    db.delete(u)
    if c:
        db.delete(c)
    db.commit()
    return {'ok': True}


@router.post("/items")
def create_item(payload: ItemIn, db: Session = Depends(get_db), _=Depends(require_roles('admin', 'super_admin'))):
    return sfe_service.create_item(db, payload.model_dump())


@router.get("/items")
def list_items(keyword: str | None = None, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return sfe_service.search_items(db, keyword)


@router.patch('/items/{item_id}')
def update_item(item_id: int, payload: dict, db: Session = Depends(get_db), _=Depends(require_roles('super_admin'))):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, '商品不存在')
    for k in ['jan', 'brand', 'name', 'spec', 'msrp_price', 'in_qty', 'is_active']:
        if k in payload:
            setattr(item, k, payload[k])
    db.commit()
    return {'ok': True}


@router.get('/items/import-template')
def item_import_template(_=Depends(require_roles('super_admin'))):
    wb = Workbook()
    ws = wb.active
    ws.title = 'items'
    ws.append(['jan', 'brand', 'name', 'spec', 'msrp_price', 'in_qty', 'is_active'])
    ws.append(['JAN00001', 'Shimano', '示例商品', '规格', 199, 1, 1])
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return StreamingResponse(bio, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': 'attachment; filename=item_template.xlsx'})


@router.post('/items/import-excel')
def import_items_excel(file: UploadFile = File(...), db: Session = Depends(get_db), _=Depends(require_roles('super_admin'))):
    wb = load_workbook(filename=BytesIO(file.file.read()))
    ws = wb.active
    created = 0
    updated = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:
            continue
        jan, brand, name, spec, msrp_price, in_qty, is_active = row[:7]
        obj = db.query(Item).filter(Item.jan == str(jan)).first()
        if obj:
            obj.brand = str(brand or obj.brand)
            obj.name = str(name or obj.name)
            obj.spec = str(spec) if spec else None
            obj.msrp_price = float(msrp_price or 0)
            obj.in_qty = int(in_qty or 1)
            obj.is_active = bool(is_active)
            updated += 1
        else:
            db.add(Item(jan=str(jan), brand=str(brand or ''), name=str(name or ''), spec=str(spec) if spec else None, msrp_price=float(msrp_price or 0), in_qty=int(in_qty or 1), is_active=bool(is_active)))
            created += 1
    db.commit()
    return {'created': created, 'updated': updated}


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


@router.post('/bills/from-orders')
def build_bill_from_orders(payload: dict, db: Session = Depends(get_db), user=Depends(require_roles('super_admin'))):
    return sfe_service.build_bill_from_orders(db, payload.get('order_ids', []), user.role, float(payload.get('sale_unit_price', 1)))


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
