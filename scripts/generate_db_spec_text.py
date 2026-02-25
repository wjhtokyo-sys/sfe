import sqlite3
from pathlib import Path
from datetime import datetime

root = Path(r"C:/sfe-system")
db_path = root / "sfe.db"
out_path = root / "docs" / "SFE_DATABASE_SPEC_TEXT.md"

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]

schema = {}
rels = []
for t in tables:
    cols = [dict(r) for r in cur.execute(f"PRAGMA table_info('{t}')")]
    fks = [dict(r) for r in cur.execute(f"PRAGMA foreign_key_list('{t}')")]
    schema[t] = {'columns': cols, 'fks': fks}
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



def field_note(name: str) -> str:
    if name.endswith('_id'):
        return '外键/关联键'
    if name in {'status', 'payment_status', 'shipping_status'}:
        return '状态字段'
    if name in {'created_at', 'archived_at', 'resolved_at', 'payment_confirmed_at', 'purchased_at'}:
        return '时间戳字段'
    if name in {'qty', 'qty_requested', 'qty_allocated', 'qty_received', 'qty_remaining'}:
        return '数量字段'
    if any(k in name for k in ['amount', 'cost', 'price', 'total']):
        return '金额字段'
    return '业务字段'


lines = []
lines.append('# SFE 数据库说明（纯文本版，可直接复制）')
lines.append('')
lines.append(f'生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
lines.append(f'数据库文件：{db_path}')
lines.append('')

lines.append('一、表清单与业务定位')
for t in tables:
    lines.append(f'- {t}：{business_desc.get(t, "（待补充）")}')
lines.append('')

lines.append('二、各表字段说明（无表格版）')
for t in tables:
    lines.append('')
    lines.append(f'【{t}】')
    lines.append(f'业务用途：{business_desc.get(t, "（待补充）")}')
    lines.append('字段说明：')
    for c in schema[t]['columns']:
        name = c['name']
        typ = c['type']
        notnull = '是' if c['notnull'] else '否'
        pk = '是' if c['pk'] else '否'
        dflt = str(c['dflt_value']) if c['dflt_value'] is not None else '无'
        note = field_note(name)
        lines.append(f"- {name}（类型: {typ}；主键: {pk}；非空: {notnull}；默认值: {dflt}；说明: {note}）")

    if schema[t]['fks']:
        lines.append('关联关系：')
        for fk in schema[t]['fks']:
            lines.append(f"- {t}.{fk['from']} -> {fk['table']}.{fk['to']}")
    else:
        lines.append('关联关系：无外键。')

lines.append('')
lines.append('三、关联关系总览')
for s, sc, d, dc in rels:
    lines.append(f'- {s}.{sc} -> {d}.{dc}')
lines.append('')

lines.append('四、核心业务动作与数据反应')
for a, r in action_notes:
    lines.append(f'- {a}：{r}')
lines.append('')

lines.append('五、状态流与变动说明')
for k, v in status_notes.items():
    lines.append(f'- {k}：{v}')
lines.append('- 进货单 checked_inbound 后不可回退。')
lines.append('- 账单生成后，关联 allocation 从 active 变为 billed，避免重复开票。')
lines.append('- FIFO 挂起任务支持部分处理，剩余数量保持 pending，直至全部处理。')
lines.append('')

lines.append('六、应用侧动态变化注意事项')
lines.append('- allocated_by 用于记录来源流程（如 purchase_checkin:PO...、fifo_manual_match:PO...），并驱动到货一览与账单候选筛选。')
lines.append('- jan_snapshot / item_name_snapshot 为历史快照字段，商品主数据变更不会回写历史单据。')
lines.append('- 超管可通过 db/table/* 通用接口直接改表，但需遵守业务状态机，避免数据不一致。')

out_path.write_text('\n'.join(lines), encoding='utf-8')
print(out_path)
