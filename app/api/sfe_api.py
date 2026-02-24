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

    new_username = str(payload.get('username', '')).strip()
    if new_username and new_username != u.username:
        exists = db.query(User).filter(User.username == new_username, User.id != user_id).first()
        if exists:
            raise HTTPException(400, '用户名已存在')
        u.username = new_username

    if 'password' in payload and payload['password']:
        u.password = payload['password']
    if 'is_active' in payload:
        u.is_active = bool(payload['is_active'])

    if u.customer_id:
        c = db.get(Customer, u.customer_id)
        if c and 'is_active' in payload:
            c.is_active = bool(payload['is_active'])
        if c and payload.get('customer_name'):
            c.name = str(payload['customer_name']).strip()

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
    try:
        raw = file.file.read()
        wb = load_workbook(filename=BytesIO(raw), data_only=True)
        ws = wb.active
    except Exception:
        raise HTTPException(400, 'Excel文件解析失败，请使用模板并保存为xlsx后重试')

    def to_float(v, default=0.0):
        if v is None or str(v).strip() == '':
            return default
        return float(v)

    def to_int(v, default=1):
        if v is None or str(v).strip() == '':
            return default
        return int(float(v))

    def to_bool(v, default=True):
        if v is None or str(v).strip() == '':
            return default
        if isinstance(v, bool):
            return v
        s = str(v).strip().lower()
        if s in {'1', 'true', 'yes', 'y', '是', '启用'}:
            return True
        if s in {'0', 'false', 'no', 'n', '否', '停用'}:
            return False
        return default

    def normalize_jan(v):
        if v is None:
            return ''
        if isinstance(v, (int, float)):
            return str(int(v))
        s = str(v).strip()
        if s.endswith('.0') and s.replace('.', '', 1).isdigit():
            return s[:-2]
        return s

    created = 0
    updated = 0
    try:
        existing = {normalize_jan(i.jan): i for i in db.query(Item).all()}
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or not row[0]:
                continue
            jan, brand, name, spec, msrp_price, in_qty, is_active = (list(row) + [None] * 7)[:7]
            jan = normalize_jan(jan)
            if not jan:
                continue

            obj = existing.get(jan)
            if obj:
                obj.brand = str(brand or obj.brand)
                obj.name = str(name or obj.name)
                obj.spec = str(spec) if spec else None
                obj.msrp_price = to_float(msrp_price, obj.msrp_price or 0)
                obj.in_qty = to_int(in_qty, obj.in_qty or 1)
                obj.is_active = to_bool(is_active, obj.is_active)
                updated += 1
            else:
                obj = Item(
                    jan=jan,
                    brand=str(brand or ''),
                    name=str(name or ''),
                    spec=str(spec) if spec else None,
                    msrp_price=to_float(msrp_price, 0),
                    in_qty=to_int(in_qty, 1),
                    is_active=to_bool(is_active, True),
                )
                db.add(obj)
                existing[jan] = obj
                created += 1
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(400, f'上传失败：{e}')

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


@router.delete('/orders/{order_id}')
def delete_order(order_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = db.get(CustomerOrder, order_id)
    if not order:
        raise HTTPException(404, '订单不存在')

    if user.role == 'customer':
        if user.customer_id != order.customer_id:
            raise HTTPException(403, '无权删除该订单')
        if (order.qty_allocated or 0) > 0:
            raise HTTPException(400, '该订单已有分配记录，无法删除')
    elif user.role != 'super_admin':
        raise HTTPException(403, '无权删除订单')

    db.delete(order)
    db.commit()
    return {'ok': True}


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
def bill_state_action(bill_id: int, payload: StateActionIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.role not in {'customer', 'super_admin', 'admin'}:
        raise HTTPException(403, '没有权限')
    bill = db.get(Bill, bill_id)
    if not bill:
        raise HTTPException(404, '账单不存在')
    if user.role == 'customer' and user.customer_id != bill.customer_id:
        raise HTTPException(403, '没有权限')
    return sfe_service.update_bill_state(db, bill_id, payload.action, user.role)


@router.patch('/bills/{bill_id}')
def update_bill(bill_id: int, payload: dict, db: Session = Depends(get_db), _=Depends(require_roles('super_admin'))):
    bill = db.get(Bill, bill_id)
    if not bill:
        raise HTTPException(404, '账单不存在')

    if 'bill_no' in payload and payload['bill_no']:
        new_no = str(payload['bill_no']).strip()
        exists = db.query(Bill).filter(Bill.bill_no == new_no, Bill.id != bill_id).first()
        if exists:
            raise HTTPException(400, '账单号已存在')
        bill.bill_no = new_no

    for k in ['status', 'payment_status', 'shipping_status', 'currency']:
        if k in payload and payload[k]:
            setattr(bill, k, payload[k])

    if 'total_amount' in payload and payload['total_amount'] is not None:
        bill.total_amount = float(payload['total_amount'])

    db.commit()
    return {'ok': True}


@router.post('/fifo/pending/{allocation_id}/resolve')
def resolve_fifo_pending(allocation_id: int, decision: StateActionIn, _=Depends(require_roles('super_admin'))):
    return {'allocation_id': allocation_id, 'decision': decision.action, 'status': 'resolved_by_super_admin'}
