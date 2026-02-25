from PIL import Image, ImageDraw, ImageFont

W, H = 2600, 1700
img = Image.new('RGB', (W, H), 'white')
d = ImageDraw.Draw(img)

try:
    font = ImageFont.truetype('arial.ttf', 20)
    font_b = ImageFont.truetype('arialbd.ttf', 22)
except Exception:
    font = ImageFont.load_default()
    font_b = font

boxes = {
    'suppliers': (80, 80, 560, 280, ['id (PK)', 'supplier_code (UQ)', 'name', 'is_active', 'created_at']),
    'purchase_orders': (650, 80, 1230, 330, ['id (PK)', 'po_no (UQ)', 'supplier_id (FK)', 'payment_status', 'status', 'total_cost', 'purchased_at', 'created_at']),
    'purchase_order_lines': (1330, 80, 1980, 360, ['id (PK)', 'purchase_order_id (FK)', 'jan', 'item_name_snapshot', 'qty', 'unit_cost', 'line_total', 'created_at']),
    'fifo_pending_tasks': (2060, 80, 2520, 360, ['id (PK)', 'purchase_order_line_id (FK)', 'source_po_no', 'jan', 'qty', 'reason_code', 'status', 'resolved_at', 'created_at']),

    'items': (80, 500, 620, 860, ['id (PK)', 'jan (UQ)', 'brand', 'name', 'spec', 'msrp_price', 'in_qty', 'is_active', 'created_at']),
    'customers': (700, 500, 1160, 760, ['id (PK)', 'name', 'is_active', 'created_at']),
    'users': (1240, 500, 1760, 840, ['id (PK)', 'username (UQ)', 'password', 'role', 'is_active', 'customer_id (FK)', 'created_at']),
    'auth_tokens': (1840, 500, 2400, 760, ['id (PK)', 'token (UQ)', 'user_id (FK)', 'created_at']),

    'customer_orders': (80, 980, 760, 1380, ['id (PK)', 'customer_id (FK)', 'item_id (FK)', 'jan_snapshot', 'item_name_snapshot', 'qty_requested', 'qty_allocated', 'status', 'created_at']),
    'inventory_lots': (840, 980, 1360, 1320, ['id (PK)', 'item_id (FK)', 'qty_received', 'qty_remaining', 'fifo_rank', 'location', 'created_at']),
    'allocations': (1440, 980, 2080, 1420, ['id (PK)', 'customer_id (FK)', 'order_line_id (FK)', 'lot_id (FK)', 'item_id (FK)', 'qty_allocated', 'fifo_rank_snapshot', 'status', 'allocated_by', 'created_at']),
    'bills': (2160, 980, 2520, 1340, ['id (PK)', 'customer_id (FK)', 'bill_no (UQ)', 'status', 'payment_status', 'shipping_status', 'total_amount', 'archived_at', 'created_at']),
    'bill_lines': (1900, 1420, 2520, 1660, ['id (PK)', 'bill_id (FK)', 'allocation_id (FK)', 'item_id (FK)', 'jan_snapshot', 'qty', 'sale_unit_price', 'line_amount', 'created_at']),
}


def draw_box(name, x1, y1, x2, y2, fields):
    d.rectangle([x1, y1, x2, y2], outline='black', width=3)
    d.rectangle([x1, y1, x2, y1+40], fill='#eef3ff', outline='black', width=3)
    d.text((x1+10, y1+8), name, fill='black', font=font_b)
    y = y1 + 52
    for f in fields:
        d.text((x1+10, y), f, fill='black', font=font)
        y += 28

for n, (x1,y1,x2,y2,fields) in boxes.items():
    draw_box(n, x1,y1,x2,y2,fields)


def center_right(box):
    x1,y1,x2,y2,_ = box
    return (x2, (y1+y2)//2)

def center_left(box):
    x1,y1,x2,y2,_ = box
    return (x1, (y1+y2)//2)

def center_bottom(box):
    x1,y1,x2,y2,_ = box
    return ((x1+x2)//2, y2)

def center_top(box):
    x1,y1,x2,y2,_ = box
    return ((x1+x2)//2, y1)

def link(a, b, label='FK'):
    ax, ay = a
    bx, by = b
    d.line([ax, ay, bx, by], fill='#cc0000', width=3)
    mx, my = (ax+bx)//2, (ay+by)//2
    d.text((mx+4, my-18), label, fill='#cc0000', font=font)

# Relationships
link(center_right(boxes['suppliers']), center_left(boxes['purchase_orders']), 'supplier_id')
link(center_right(boxes['purchase_orders']), center_left(boxes['purchase_order_lines']), 'purchase_order_id')
link(center_right(boxes['purchase_order_lines']), center_left(boxes['fifo_pending_tasks']), 'purchase_order_line_id')

link(center_bottom(boxes['customers']), center_top(boxes['customer_orders']), 'customer_id')
link(center_bottom(boxes['items']), center_top(boxes['customer_orders']), 'item_id')
link(center_bottom(boxes['items']), center_top(boxes['inventory_lots']), 'item_id')
link(center_bottom(boxes['users']), center_top(boxes['auth_tokens']), 'user_id')
link(center_bottom(boxes['customers']), center_top(boxes['users']), 'customer_id')

link(center_right(boxes['customer_orders']), center_left(boxes['allocations']), 'order_line_id')
link(center_right(boxes['inventory_lots']), center_left(boxes['allocations']), 'lot_id')
link(center_bottom(boxes['items']), center_top(boxes['allocations']), 'item_id')
link(center_bottom(boxes['customers']), center_top(boxes['allocations']), 'customer_id')

link(center_right(boxes['allocations']), center_left(boxes['bill_lines']), 'allocation_id')
link(center_bottom(boxes['items']), center_top(boxes['bill_lines']), 'item_id')
link(center_bottom(boxes['bills']), center_top(boxes['bill_lines']), 'bill_id')
link(center_bottom(boxes['customers']), center_top(boxes['bills']), 'customer_id')

d.text((20, 1640), 'SFE ER Diagram (auto-generated) - includes all current tables and FK relations', fill='black', font=font)

out = r'C:\sfe-system\docs\images\SFE_ER_LATEST.jpg'
img.save(out, quality=95)
print(out)
