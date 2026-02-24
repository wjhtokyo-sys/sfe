from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from openpyxl import Workbook, load_workbook
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_roles
from app.core.database import get_db
from app.models.entities import Allocation, Bill, BillLine, Customer, CustomerOrder, FifoPendingTask, InventoryLot, Item, PurchaseOrder, PurchaseOrderLine, Supplier, User
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


@router.get('/suppliers')
def list_suppliers(db: Session = Depends(get_db), _=Depends(require_roles('super_admin'))):
    return db.query(Supplier).order_by(Supplier.id.desc()).all()


@router.post('/suppliers')
def create_supplier(payload: dict, db: Session = Depends(get_db), _=Depends(require_roles('super_admin'))):
    code = str(payload.get('supplier_code', '')).strip()
    name = str(payload.get('name', '')).strip()
    if not code or not name:
        raise HTTPException(400, '请填写供应商编码和供应商名')
    if db.query(Supplier).filter(Supplier.supplier_code == code).first():
        raise HTTPException(400, '供应商编码已存在')
    obj = Supplier(supplier_code=code, name=name, is_active=True)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.patch('/suppliers/{supplier_id}')
def update_supplier(supplier_id: int, payload: dict, db: Session = Depends(get_db), _=Depends(require_roles('super_admin'))):
    obj = db.get(Supplier, supplier_id)
    if not obj:
        raise HTTPException(404, '供应商不存在')
    if payload.get('supplier_code'):
        code = str(payload.get('supplier_code')).strip()
        exists = db.query(Supplier).filter(Supplier.supplier_code == code, Supplier.id != supplier_id).first()
        if exists:
            raise HTTPException(400, '供应商编码已存在')
        obj.supplier_code = code
    if payload.get('name'):
        obj.name = str(payload.get('name')).strip()
    if 'is_active' in payload:
        obj.is_active = bool(payload.get('is_active'))
    db.commit()
    return {'ok': True}


@router.delete('/suppliers/{supplier_id}')
def delete_supplier(supplier_id: int, db: Session = Depends(get_db), _=Depends(require_roles('super_admin'))):
    obj = db.get(Supplier, supplier_id)
    if not obj:
        raise HTTPException(404, '供应商不存在')
    db.delete(obj)
    db.commit()
    return {'ok': True}


@router.get('/purchase-orders/import-template')
def purchase_order_import_template(_=Depends(require_roles('super_admin'))):
    wb = Workbook()
    ws = wb.active
    ws.title = 'purchase_order'
    ws.append(['jan', 'item_name', 'qty', 'unit_cost', 'payment_status', 'purchased_at'])
    ws.append(['JAN00001', '示例货品', 10, 120, 'unpaid', '2026-02-25'])
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return StreamingResponse(bio, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': 'attachment; filename=purchase_order_template.xlsx'})


@router.post('/purchase-orders/import-excel')
def import_purchase_order_excel(supplier_id: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db), _=Depends(require_roles('super_admin'))):
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(400, '供应商不存在，请先选择供应商')

    try:
        wb = load_workbook(filename=BytesIO(file.file.read()), data_only=True)
        ws = wb.active
        header = [str(c).strip().lower() if c is not None else '' for c in next(ws.iter_rows(min_row=1, max_row=1, values_only=True))]
        rows = [r for r in ws.iter_rows(min_row=2, values_only=True) if r and r[0]]
        if not rows:
            raise HTTPException(400, '模板没有可导入数据')

        po_no = f"PO{datetime.now().strftime('%Y%m%d%H%M%S')}{supplier.supplier_code}"
        while db.query(PurchaseOrder).filter(PurchaseOrder.po_no == po_no).first():
            po_no = f"PO{datetime.now().strftime('%Y%m%d%H%M%S%f')}{supplier.supplier_code}"

        # 支持两种模板：
        # A) purchase模板: jan,item_name,qty,unit_cost,payment_status,purchased_at
        # B) item模板兼容: jan,brand,name,spec,msrp_price,in_qty,is_active
        if header[:6] == ['jan', 'item_name', 'qty', 'unit_cost', 'payment_status', 'purchased_at']:
            payment_status = str(rows[0][4] or 'unpaid')
            purchased_at = rows[0][5] if isinstance(rows[0][5], datetime) else datetime.now()
            parsed = [
                {
                    'jan': str(r[0]).strip(),
                    'item_name': str(r[1]).strip(),
                    'qty': int(float(r[2] or 0)),
                    'unit_cost': float(r[3] or 0),
                }
                for r in rows
            ]
        else:
            payment_status = 'unpaid'
            purchased_at = datetime.now()
            parsed = [
                {
                    'jan': str(r[0]).strip(),
                    'item_name': str((r[2] if len(r) > 2 else '') or r[0]).strip(),
                    'qty': int(float((r[5] if len(r) > 5 else 0) or 0)),
                    'unit_cost': float((r[4] if len(r) > 4 else 0) or 0),
                }
                for r in rows
            ]

        po = PurchaseOrder(po_no=po_no, supplier_id=supplier_id, payment_status=payment_status, status='created_unchecked', purchased_at=purchased_at)
        db.add(po)
        db.flush()
        total = 0.0
        for p in parsed:
            line_total = p['qty'] * p['unit_cost']
            total += line_total
            db.add(PurchaseOrderLine(purchase_order_id=po.id, jan=p['jan'], item_name_snapshot=p['item_name'], qty=p['qty'], unit_cost=p['unit_cost'], line_total=line_total))
        po.total_cost = total
        db.commit()
        return {'ok': True, 'po_no': po_no, 'rows': len(parsed)}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(400, f'导入失败：{e}')


@router.get('/purchase-orders')
def list_purchase_orders(db: Session = Depends(get_db), _=Depends(require_roles('super_admin'))):
    return db.query(PurchaseOrder).order_by(PurchaseOrder.id.desc()).all()


@router.post('/purchase-orders/lines')
def add_purchase_order_line(payload: dict, db: Session = Depends(get_db), _=Depends(require_roles('super_admin'))):
    po_no = str(payload.get('po_no', '')).strip()
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_no == po_no).first()
    if not po:
        po = PurchaseOrder(
            po_no=po_no,
            supplier_id=int(payload.get('supplier_id')),
            payment_status=str(payload.get('payment_status') or 'unpaid'),
            status='created_unchecked',
            purchased_at=payload.get('purchased_at'),
        )
        db.add(po)
        db.flush()
    qty = int(payload.get('qty') or 0)
    unit_cost = float(payload.get('unit_cost') or 0)
    line_total = qty * unit_cost
    db.add(PurchaseOrderLine(
        purchase_order_id=po.id,
        jan=str(payload.get('jan')).strip(),
        item_name_snapshot=str(payload.get('item_name')).strip(),
        qty=qty,
        unit_cost=unit_cost,
        line_total=line_total,
    ))
    po.total_cost = float(po.total_cost or 0) + line_total
    db.commit()
    return {'ok': True}


@router.delete('/purchase-orders/{po_id}')
def delete_purchase_order(po_id: int, db: Session = Depends(get_db), _=Depends(require_roles('super_admin'))):
    po = db.get(PurchaseOrder, po_id)
    if not po:
        raise HTTPException(404, '进货单不存在')
    lines = db.query(PurchaseOrderLine).filter(PurchaseOrderLine.purchase_order_id == po.id).all()
    for ln in lines:
        db.delete(ln)
    db.delete(po)
    db.commit()
    return {'ok': True}


@router.post('/purchase-orders/{po_id}/status')
def update_purchase_order_status(po_id: int, payload: dict, db: Session = Depends(get_db), _=Depends(require_roles('super_admin'))):
    po = db.get(PurchaseOrder, po_id)
    if not po:
        raise HTTPException(404, '进货单不存在')
    new_status = str(payload.get('status', '')).strip()
    if new_status not in {'created_unchecked', 'checked_inbound'}:
        raise HTTPException(400, '状态不支持')
    if po.status == 'checked_inbound':
        raise HTTPException(400, '进货单已盘点入库，不能回退')
    if new_status == 'checked_inbound':
        lines = db.query(PurchaseOrderLine).filter(PurchaseOrderLine.purchase_order_id == po.id).all()
        for ln in lines:
            matches = db.query(CustomerOrder).filter(CustomerOrder.jan_snapshot == ln.jan, CustomerOrder.status == 'open').all()
            customer_ids = sorted({m.customer_id for m in matches})
            if len(customer_ids) >= 2:
                db.add(FifoPendingTask(purchase_order_line_id=ln.id, source_po_no=po.po_no, jan=ln.jan, item_name=ln.item_name_snapshot, qty=ln.qty, reason_code='multi_customer_match', reason_text='JAN命中多个客户未完成订单，需人工处理', status='pending'))
                continue
            if len(customer_ids) == 0:
                db.add(FifoPendingTask(purchase_order_line_id=ln.id, source_po_no=po.po_no, jan=ln.jan, item_name=ln.item_name_snapshot, qty=ln.qty, reason_code='no_order_match', reason_text='未命中客户订单，需人工处理后再入库', status='pending'))
                continue
            lot = InventoryLot(item_id=matches[0].item_id, qty_received=ln.qty, qty_remaining=ln.qty, fifo_rank=db.query(InventoryLot).filter(InventoryLot.item_id == matches[0].item_id).count() + 1, location='PO_CHECKED')
            db.add(lot)
        po.status = 'checked_inbound'
    else:
        po.status = new_status
    db.commit()
    return {'ok': True}


@router.get('/fifo/pending')
def list_fifo_pending(db: Session = Depends(get_db), _=Depends(require_roles('super_admin'))):
    return db.query(FifoPendingTask).order_by(FifoPendingTask.id.desc()).all()


@router.post('/fifo/pending/{task_id}/resolve')
def resolve_fifo_pending_task(task_id: int, payload: dict, db: Session = Depends(get_db), user=Depends(require_roles('super_admin'))):
    task = db.get(FifoPendingTask, task_id)
    if not task:
        raise HTTPException(404, '挂起任务不存在')
    if task.status == 'resolved':
        raise HTTPException(400, '该任务已处理')
    action = str(payload.get('action', '')).strip()
    if action not in {'inbound_to_order', 'inbound_stock', 'close_only'}:
        raise HTTPException(400, '不支持的处理动作')

    if action in {'inbound_to_order', 'inbound_stock'}:
        line = db.get(PurchaseOrderLine, task.purchase_order_line_id) if task.purchase_order_line_id else None
        if not line:
            raise HTTPException(400, '来源进货明细不存在')
        item = db.query(Item).filter(Item.jan == line.jan).first()
        if not item:
            item = Item(jan=line.jan, brand='-', name=line.item_name_snapshot or line.jan, spec=None, msrp_price=0, in_qty=1, is_active=True)
            db.add(item)
            db.flush()
        lot = InventoryLot(item_id=item.id, qty_received=line.qty, qty_remaining=line.qty, fifo_rank=db.query(InventoryLot).filter(InventoryLot.item_id == item.id).count() + 1, location='FIFO_PENDING')
        db.add(lot)

    task.status = 'resolved'
    task.resolution_note = action
    task.resolved_by = 'super_admin'
    task.resolved_at = __import__('datetime').datetime.utcnow()
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


@router.delete('/items/{item_id}')
def delete_item(item_id: int, db: Session = Depends(get_db), _=Depends(require_roles('super_admin'))):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, '商品不存在')
    db.delete(item)
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


@router.get('/bills/{bill_id}/lines')
def bill_lines(bill_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    bill = db.get(Bill, bill_id)
    if not bill:
        raise HTTPException(404, '账单不存在')
    if user.role == 'customer' and user.customer_id != bill.customer_id:
        raise HTTPException(403, '没有权限')

    lines = db.query(BillLine).filter(BillLine.bill_id == bill_id).order_by(BillLine.id.asc()).all()
    return lines


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


@router.post('/fifo/pending-legacy/{allocation_id}/resolve')
def resolve_fifo_pending(allocation_id: int, decision: StateActionIn, _=Depends(require_roles('super_admin'))):
    return {'allocation_id': allocation_id, 'decision': decision.action, 'status': 'legacy_resolved'}
