import sqlite3
from pathlib import Path
from datetime import datetime

root = Path(r"C:/sfe-system")
db_path = root / "sfe.db"
docs = root / "docs"
docs.mkdir(exist_ok=True)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]

schema = {}
rels = []
for t in tables:
    cols = [dict(r) for r in cur.execute(f"PRAGMA table_info('{t}')")]
    fks = [dict(r) for r in cur.execute(f"PRAGMA foreign_key_list('{t}')")]
    idxs = [dict(r) for r in cur.execute(f"PRAGMA index_list('{t}')")]
    schema[t] = {'columns': cols, 'fks': fks, 'indexes': idxs}
    for fk in fks:
        rels.append((t, fk['from'], fk['table'], fk['to']))

business_desc = {
    'users':'系统账号（super_admin/admin/customer）及客户账号归属',
    'auth_tokens':'登录令牌，绑定用户会话',
    'customers':'客户主数据（客户名称、启用状态）',
    'suppliers':'供应商主数据',
    'items':'商品主数据（JAN、品牌、品名、规格、标价）',
    'purchase_orders':'进货单头（供应商、状态、成本、付款状态）',
    'purchase_order_lines':'进货单行（JAN、数量、进货单价）',
    'fifo_pending_tasks':'FIFO待处理任务（多客户命中/无订单命中等）',
    'customer_orders':'客户下单明细（需求数量、已分配数量、状态）',
    'inventory_lots':'库存批次（入库量、剩余量、FIFO顺序）',
    'allocations':'分配记录（订单行 x 批次 x 客户）',
    'bills':'账单头（金额、支付与物流状态）',
    'bill_lines':'账单行（来自allocation，记录售价和行金额）',
}

status_notes = {
    'purchase_orders.status':'created_unchecked -> checked_inbound（不可逆）',
    'purchase_orders.payment_status':'unpaid -> paid',
    'customer_orders.status':'open -> closed',
    'allocations.status':'active -> billed',
    'bills.stage':'created -> paid -> confirmed -> shipped -> received -> archived',
    'fifo_pending_tasks.status':'pending -> resolved',
}

action_notes = [
    ('导入/新增进货单', '创建 purchase_orders + purchase_order_lines，状态初始 created_unchecked'),
    ('进货单盘点入库', '按JAN匹配开放订单；单客户自动分配，多客户/无匹配生成 fifo_pending_tasks'),
    ('FIFO人工处理', '在 fifo_pending_tasks 上执行匹配订单/转无匹配/指定客户，写入 allocations + inventory_lots'),
    ('客户下单', '写入 customer_orders，等待分配'),
    ('生成账单（到货一览）', '使用 active allocations 生成 bills + bill_lines，并将 allocation 置为 billed'),
    ('账单状态推进', '按角色和状态机推进到 archived；客户仅可执行 pay/confirm_receipt'),
    ('删除保护', '有外键引用时拒绝删除，避免脏数据；已盘点明细禁止删除'),
]

md = []
md.append('# SFE 数据库说明（自动生成）')
md.append('')
md.append(f'- 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
md.append(f'- 数据库文件: `{db_path}`')
md.append('')
md.append('## 1) 表清单与业务定位')
for t in tables:
    md.append(f'- `{t}`: {business_desc.get(t, "（待补充）")}')

md.append('')
md.append('## 2) 各表字段说明')
for t in tables:
    md.append(f'### `{t}`')
    md.append('')
    md.append('| 字段 | 类型 | 非空 | 主键 | 默认值 | 说明 |')
    md.append('|---|---|---|---|---|---|')
    for c in schema[t]['columns']:
        name = c['name']
        typ = c['type']
        notnull = 'Y' if c['notnull'] else 'N'
        pk = 'Y' if c['pk'] else 'N'
        dflt = str(c['dflt_value']) if c['dflt_value'] is not None else ''
        note = ''
        if name.endswith('_id'):
            note = '外键/关联键'
        elif name in ['status', 'payment_status', 'shipping_status']:
            note = '状态字段'
        elif name in ['created_at', 'archived_at', 'resolved_at', 'payment_confirmed_at', 'purchased_at']:
            note = '时间戳'
        elif name in ['qty', 'qty_requested', 'qty_allocated', 'qty_received', 'qty_remaining']:
            note = '数量字段'
        elif 'amount' in name or 'cost' in name or 'price' in name or 'total' in name:
            note = '金额字段'
        md.append(f'| `{name}` | `{typ}` | {notnull} | {pk} | `{dflt}` | {note} |')
    if schema[t]['fks']:
        md.append('')
        md.append('外键关系:')
        for fk in schema[t]['fks']:
            md.append(f"- `{t}.{fk['from']}` -> `{fk['table']}.{fk['to']}`")
    md.append('')

md.append('## 3) 关联关系总览')
for s, sc, d, dc in rels:
    md.append(f'- `{s}.{sc}` -> `{d}.{dc}`')

md.append('')
md.append('## 4) 核心业务动作与数据反应')
for a, r in action_notes:
    md.append(f'- **{a}**：{r}')

md.append('')
md.append('## 5) 状态流与变动说明')
for k, v in status_notes.items():
    md.append(f'- `{k}`: {v}')
md.append('- 进货单 `checked_inbound` 后不可回退。')
md.append('- 账单生成后，关联 allocation 从 `active` 变为 `billed`，避免重复开票。')
md.append('- FIFO 挂起任务支持部分处理；剩余数量继续保留在 pending。')
md.append('')
md.append('## 6) 应用侧动态变化注意事项')
md.append('- `allocated_by` 记录来源流程（如 `purchase_checkin:PO...`、`fifo_manual_match:PO...`），用于到货/账单候选筛选。')
md.append('- `jan_snapshot` / `item_name_snapshot` 用于冻结历史快照，避免商品主数据变更影响历史单据。')
md.append('- `db/table/*` 通用接口支持超管直接改表，需注意和业务状态机一致性。')

spec_path = docs / 'SFE_DATABASE_SPEC.md'
spec_path.write_text('\n'.join(md), encoding='utf-8')

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

fig, ax = plt.subplots(figsize=(16, 9), dpi=150)
ax.set_xlim(0, 16)
ax.set_ylim(0, 9)
ax.axis('off')

def box(x, y, w, h, text, color='#E8F0FE'):
    r = Rectangle((x, y), w, h, facecolor=color, edgecolor='#2b4c7e', linewidth=1.5)
    ax.add_patch(r)
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=10)

def arrow(x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='->', mutation_scale=12, linewidth=1.3, color='#333'))

box(0.6, 6.8, 2.6, 1.1, 'Supplier / Receiving\ncreate PO')
box(3.8, 6.8, 2.8, 1.1, 'PO import\npurchase_orders + lines')
box(7.2, 6.8, 2.8, 1.1, 'Stock check-in\nchecked_inbound')
box(10.6, 6.8, 2.8, 1.1, 'FIFO auto allocation\nor create pending task')
box(13.8, 6.8, 1.8, 1.1, 'FIFO manual\nresolution')

box(0.8, 4.7, 2.8, 1.1, 'Customer order\ncustomer_orders(open)', '#FFF4E5')
box(4.2, 4.7, 2.8, 1.1, 'allocations(active)\n+ inventory_lots', '#FFF4E5')
box(7.6, 4.7, 2.8, 1.1, 'Arrival bill candidates\nfiltered by source', '#FFF4E5')
box(11.0, 4.7, 2.8, 1.1, 'Build bill\nbills + bill_lines', '#FFF4E5')

box(4.6, 2.6, 3.2, 1.1, 'Bill stage flow\ncreated→paid→confirmed', '#E8F5E9')
box(8.5, 2.6, 3.8, 1.1, 'Shipping / receive / archive\nshipped→received→archived', '#E8F5E9')

arrow(3.2, 7.35, 3.8, 7.35)
arrow(6.6, 7.35, 7.2, 7.35)
arrow(10.0, 7.35, 10.6, 7.35)
arrow(13.4, 7.35, 13.8, 7.35)
arrow(2.2, 5.8, 4.8, 5.8)
arrow(7.0, 5.25, 7.6, 5.25)
arrow(10.4, 5.25, 11.0, 5.25)
arrow(6.8, 4.7, 6.2, 3.7)
arrow(10.8, 4.7, 10.2, 3.7)
arrow(7.8, 3.15, 8.5, 3.15)
arrow(11.5, 6.8, 9.0, 5.8)
ax.text(0.6, 8.35, 'SFE Business Flow Overview', fontsize=16, fontweight='bold')
ax.text(0.6, 0.8, 'Note: multi-customer match / no-match cases go to fifo_pending_tasks for super-admin handling.', fontsize=9, color='#555')
fig.savefig(docs / 'SFE_BUSINESS_FLOW.jpg', format='jpg', bbox_inches='tight')
plt.close(fig)

fig, ax = plt.subplots(figsize=(18, 10), dpi=150)
ax.set_xlim(0, 18)
ax.set_ylim(0, 10)
ax.axis('off')

pos = {
    'users': (0.6, 7.7), 'auth_tokens': (0.6, 5.9), 'customers': (3.5, 7.7), 'suppliers': (3.5, 5.9),
    'items': (6.4, 7.7), 'purchase_orders': (6.4, 5.9), 'purchase_order_lines': (9.7, 5.9),
    'customer_orders': (9.7, 7.7), 'inventory_lots': (12.8, 7.7), 'allocations': (12.8, 5.9),
    'bills': (15.4, 7.7), 'bill_lines': (15.4, 5.9), 'fifo_pending_tasks': (9.7, 4.1)
}

for t, (x, y) in pos.items():
    cols = [c['name'] for c in schema.get(t, {}).get('columns', [])][:4]
    label = t + '\n' + '\n'.join(cols)
    r = Rectangle((x, y), 2.3, 1.4, facecolor='#eef7ff', edgecolor='#245', linewidth=1.2)
    ax.add_patch(r)
    ax.text(x + 1.15, y + 0.7, label, ha='center', va='center', fontsize=8)

def center(t):
    x, y = pos[t]
    return (x + 1.15, y + 0.7)

for s, sc, d, dc in rels:
    if s in pos and d in pos:
        x1, y1 = center(s)
        x2, y2 = center(d)
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>', mutation_scale=10, linewidth=0.9, color='#555', alpha=0.8))

ax.text(0.6, 9.6, 'SFE Database ER Diagram (from current SQLite instance)', fontsize=16, fontweight='bold')
fig.savefig(docs / 'SFE_DATABASE_ER.jpg', format='jpg', bbox_inches='tight')
plt.close(fig)

print('Generated files:')
print(spec_path)
print(docs / 'SFE_BUSINESS_FLOW.jpg')
print(docs / 'SFE_DATABASE_ER.jpg')
