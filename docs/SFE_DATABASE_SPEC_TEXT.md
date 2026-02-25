# SFE 数据库说明（纯文本版，可直接复制）

生成时间：2026-02-26 04:10:48
数据库文件：C:\sfe-system\sfe.db

一、表清单与业务定位
- allocations：分配记录（订单行 x 批次 x 客户）
- auth_tokens：登录令牌，绑定用户会话
- bill_lines：账单行（来自allocation，记录售价和行金额）
- bills：账单头（金额、支付与物流状态）
- customer_orders：客户下单明细（需求数量、已分配数量、状态）
- customers：客户主数据（客户名称、启用状态）
- fifo_pending_tasks：FIFO待处理任务（多客户命中/无订单命中等）
- inventory_lots：库存批次（入库量、剩余量、FIFO顺序）
- items：商品主数据（JAN、品牌、品名、规格、标价）
- purchase_order_lines：进货单行（JAN、数量、进货单价）
- purchase_orders：进货单头（供应商、状态、成本、付款状态）
- suppliers：供应商主数据
- users：系统账号（super_admin/admin/customer）及客户账号归属

二、各表字段说明（无表格版）

【allocations】
业务用途：分配记录（订单行 x 批次 x 客户）
字段说明：
- id（类型: INTEGER；主键: 是；非空: 是；默认值: 无；说明: 业务字段）
- customer_id（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 外键/关联键）
- order_line_id（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 外键/关联键）
- lot_id（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 外键/关联键）
- item_id（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 外键/关联键）
- qty_allocated（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 数量字段）
- fifo_rank_snapshot（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- status（类型: VARCHAR(16)；主键: 否；非空: 是；默认值: 无；说明: 状态字段）
- allocated_by（类型: VARCHAR(64)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- created_at（类型: DATETIME；主键: 否；非空: 是；默认值: 无；说明: 时间戳字段）
关联关系：
- allocations.item_id -> items.id
- allocations.lot_id -> inventory_lots.id
- allocations.order_line_id -> customer_orders.id
- allocations.customer_id -> customers.id

【auth_tokens】
业务用途：登录令牌，绑定用户会话
字段说明：
- id（类型: INTEGER；主键: 是；非空: 是；默认值: 无；说明: 业务字段）
- token（类型: VARCHAR(255)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- user_id（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 外键/关联键）
- created_at（类型: DATETIME；主键: 否；非空: 是；默认值: 无；说明: 时间戳字段）
关联关系：
- auth_tokens.user_id -> users.id

【bill_lines】
业务用途：账单行（来自allocation，记录售价和行金额）
字段说明：
- id（类型: INTEGER；主键: 是；非空: 是；默认值: 无；说明: 业务字段）
- bill_id（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 外键/关联键）
- allocation_id（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 外键/关联键）
- item_id（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 外键/关联键）
- jan_snapshot（类型: VARCHAR(64)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- item_name_snapshot（类型: VARCHAR(255)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- qty（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 数量字段）
- sale_unit_price（类型: FLOAT；主键: 否；非空: 是；默认值: 无；说明: 金额字段）
- line_amount（类型: FLOAT；主键: 否；非空: 是；默认值: 无；说明: 金额字段）
- created_at（类型: DATETIME；主键: 否；非空: 是；默认值: 无；说明: 时间戳字段）
关联关系：
- bill_lines.item_id -> items.id
- bill_lines.allocation_id -> allocations.id
- bill_lines.bill_id -> bills.id

【bills】
业务用途：账单头（金额、支付与物流状态）
字段说明：
- id（类型: INTEGER；主键: 是；非空: 是；默认值: 无；说明: 业务字段）
- customer_id（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 外键/关联键）
- bill_no（类型: VARCHAR(32)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- status（类型: VARCHAR(16)；主键: 否；非空: 是；默认值: 无；说明: 状态字段）
- payment_status（类型: VARCHAR(16)；主键: 否；非空: 是；默认值: 无；说明: 状态字段）
- shipping_status（类型: VARCHAR(16)；主键: 否；非空: 是；默认值: 无；说明: 状态字段）
- total_amount（类型: FLOAT；主键: 否；非空: 是；默认值: 无；说明: 金额字段）
- currency（类型: VARCHAR(8)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- payment_confirmed_at（类型: DATETIME；主键: 否；非空: 否；默认值: 无；说明: 时间戳字段）
- created_at（类型: DATETIME；主键: 否；非空: 是；默认值: 无；说明: 时间戳字段）
- archived_at（类型: DATETIME；主键: 否；非空: 否；默认值: 无；说明: 时间戳字段）
关联关系：
- bills.customer_id -> customers.id

【customer_orders】
业务用途：客户下单明细（需求数量、已分配数量、状态）
字段说明：
- id（类型: INTEGER；主键: 是；非空: 是；默认值: 无；说明: 业务字段）
- customer_id（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 外键/关联键）
- item_id（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 外键/关联键）
- jan_snapshot（类型: VARCHAR(64)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- item_name_snapshot（类型: VARCHAR(255)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- qty_requested（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 数量字段）
- qty_allocated（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 数量字段）
- status（类型: VARCHAR(16)；主键: 否；非空: 是；默认值: 无；说明: 状态字段）
- created_at（类型: DATETIME；主键: 否；非空: 是；默认值: 无；说明: 时间戳字段）
关联关系：
- customer_orders.item_id -> items.id
- customer_orders.customer_id -> customers.id

【customers】
业务用途：客户主数据（客户名称、启用状态）
字段说明：
- id（类型: INTEGER；主键: 是；非空: 是；默认值: 无；说明: 业务字段）
- name（类型: VARCHAR(100)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- phone（类型: VARCHAR(50)；主键: 否；非空: 否；默认值: 无；说明: 业务字段）
- email（类型: VARCHAR(100)；主键: 否；非空: 否；默认值: 无；说明: 业务字段）
- note（类型: VARCHAR(255)；主键: 否；非空: 否；默认值: 无；说明: 业务字段）
- created_at（类型: DATETIME；主键: 否；非空: 否；默认值: 无；说明: 时间戳字段）
- is_active（类型: BOOLEAN；主键: 否；非空: 否；默认值: 1；说明: 业务字段）
关联关系：无外键。

【fifo_pending_tasks】
业务用途：FIFO待处理任务（多客户命中/无订单命中等）
字段说明：
- id（类型: INTEGER；主键: 是；非空: 是；默认值: 无；说明: 业务字段）
- purchase_order_line_id（类型: INTEGER；主键: 否；非空: 否；默认值: 无；说明: 外键/关联键）
- source_po_no（类型: VARCHAR(64)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- jan（类型: VARCHAR(64)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- item_name（类型: VARCHAR(255)；主键: 否；非空: 否；默认值: 无；说明: 业务字段）
- qty（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 数量字段）
- reason_code（类型: VARCHAR(64)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- reason_text（类型: TEXT；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- status（类型: VARCHAR(16)；主键: 否；非空: 是；默认值: 无；说明: 状态字段）
- resolution_note（类型: TEXT；主键: 否；非空: 否；默认值: 无；说明: 业务字段）
- resolved_by（类型: VARCHAR(64)；主键: 否；非空: 否；默认值: 无；说明: 业务字段）
- resolved_at（类型: DATETIME；主键: 否；非空: 否；默认值: 无；说明: 时间戳字段）
- created_at（类型: DATETIME；主键: 否；非空: 是；默认值: 无；说明: 时间戳字段）
关联关系：
- fifo_pending_tasks.purchase_order_line_id -> purchase_order_lines.id

【inventory_lots】
业务用途：库存批次（入库量、剩余量、FIFO顺序）
字段说明：
- id（类型: INTEGER；主键: 是；非空: 是；默认值: 无；说明: 业务字段）
- item_id（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 外键/关联键）
- qty_received（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 数量字段）
- qty_remaining（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 数量字段）
- fifo_rank（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- location（类型: VARCHAR(128)；主键: 否；非空: 否；默认值: 无；说明: 业务字段）
- created_at（类型: DATETIME；主键: 否；非空: 是；默认值: 无；说明: 时间戳字段）
关联关系：
- inventory_lots.item_id -> items.id

【items】
业务用途：商品主数据（JAN、品牌、品名、规格、标价）
字段说明：
- id（类型: INTEGER；主键: 是；非空: 是；默认值: 无；说明: 业务字段）
- jan（类型: VARCHAR(64)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- brand（类型: VARCHAR(128)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- name（类型: VARCHAR(255)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- spec（类型: VARCHAR(255)；主键: 否；非空: 否；默认值: 无；说明: 业务字段）
- msrp_price（类型: FLOAT；主键: 否；非空: 是；默认值: 无；说明: 金额字段）
- in_qty（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- is_active（类型: BOOLEAN；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- created_at（类型: DATETIME；主键: 否；非空: 是；默认值: 无；说明: 时间戳字段）
关联关系：无外键。

【purchase_order_lines】
业务用途：进货单行（JAN、数量、进货单价）
字段说明：
- id（类型: INTEGER；主键: 是；非空: 是；默认值: 无；说明: 业务字段）
- purchase_order_id（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 外键/关联键）
- jan（类型: VARCHAR(64)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- item_name_snapshot（类型: VARCHAR(255)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- qty（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 数量字段）
- unit_cost（类型: FLOAT；主键: 否；非空: 是；默认值: 无；说明: 金额字段）
- line_total（类型: FLOAT；主键: 否；非空: 是；默认值: 无；说明: 金额字段）
- created_at（类型: DATETIME；主键: 否；非空: 是；默认值: 无；说明: 时间戳字段）
关联关系：
- purchase_order_lines.purchase_order_id -> purchase_orders.id

【purchase_orders】
业务用途：进货单头（供应商、状态、成本、付款状态）
字段说明：
- id（类型: INTEGER；主键: 是；非空: 是；默认值: 无；说明: 业务字段）
- po_no（类型: VARCHAR(64)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- supplier_id（类型: INTEGER；主键: 否；非空: 是；默认值: 无；说明: 外键/关联键）
- payment_status（类型: VARCHAR(16)；主键: 否；非空: 是；默认值: 无；说明: 状态字段）
- status（类型: VARCHAR(32)；主键: 否；非空: 是；默认值: 无；说明: 状态字段）
- total_cost（类型: FLOAT；主键: 否；非空: 是；默认值: 无；说明: 金额字段）
- purchased_at（类型: DATETIME；主键: 否；非空: 是；默认值: 无；说明: 时间戳字段）
- created_at（类型: DATETIME；主键: 否；非空: 是；默认值: 无；说明: 时间戳字段）
关联关系：
- purchase_orders.supplier_id -> suppliers.id

【suppliers】
业务用途：供应商主数据
字段说明：
- id（类型: INTEGER；主键: 是；非空: 是；默认值: 无；说明: 业务字段）
- supplier_code（类型: VARCHAR(64)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- name（类型: VARCHAR(128)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- is_active（类型: BOOLEAN；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- created_at（类型: DATETIME；主键: 否；非空: 是；默认值: 无；说明: 时间戳字段）
关联关系：无外键。

【users】
业务用途：系统账号（super_admin/admin/customer）及客户账号归属
字段说明：
- id（类型: INTEGER；主键: 是；非空: 是；默认值: 无；说明: 业务字段）
- username（类型: VARCHAR(64)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- password（类型: VARCHAR(128)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- role（类型: VARCHAR(32)；主键: 否；非空: 是；默认值: 无；说明: 业务字段）
- customer_id（类型: INTEGER；主键: 否；非空: 否；默认值: 无；说明: 外键/关联键）
- created_at（类型: DATETIME；主键: 否；非空: 是；默认值: 无；说明: 时间戳字段）
- is_active（类型: BOOLEAN；主键: 否；非空: 否；默认值: 1；说明: 业务字段）
关联关系：
- users.customer_id -> customers.id

三、关联关系总览
- allocations.item_id -> items.id
- allocations.lot_id -> inventory_lots.id
- allocations.order_line_id -> customer_orders.id
- allocations.customer_id -> customers.id
- auth_tokens.user_id -> users.id
- bill_lines.item_id -> items.id
- bill_lines.allocation_id -> allocations.id
- bill_lines.bill_id -> bills.id
- bills.customer_id -> customers.id
- customer_orders.item_id -> items.id
- customer_orders.customer_id -> customers.id
- fifo_pending_tasks.purchase_order_line_id -> purchase_order_lines.id
- inventory_lots.item_id -> items.id
- purchase_order_lines.purchase_order_id -> purchase_orders.id
- purchase_orders.supplier_id -> suppliers.id
- users.customer_id -> customers.id

四、核心业务动作与数据反应
- 导入/新增进货单：创建 purchase_orders + purchase_order_lines，状态初始 created_unchecked
- 进货单盘点入库：按JAN匹配开放订单；单客户自动分配，多客户/无匹配生成 fifo_pending_tasks
- FIFO人工处理：在 fifo_pending_tasks 上执行匹配订单/转无匹配/指定客户，写入 allocations + inventory_lots
- 客户下单：写入 customer_orders，等待分配
- 生成账单（到货一览）：使用 active allocations 生成 bills + bill_lines，并将 allocation 置为 billed
- 账单状态推进：按角色和状态机推进到 archived；客户仅可执行 pay/confirm_receipt
- 删除保护：有外键引用时拒绝删除，避免脏数据；已盘点明细禁止删除

五、状态流与变动说明
- purchase_orders.status：created_unchecked -> checked_inbound（不可逆）
- purchase_orders.payment_status：unpaid -> paid
- customer_orders.status：open -> closed
- allocations.status：active -> billed
- bills.stage：created -> paid -> confirmed -> shipped -> received -> archived
- fifo_pending_tasks.status：pending -> resolved
- 进货单 checked_inbound 后不可回退。
- 账单生成后，关联 allocation 从 active 变为 billed，避免重复开票。
- FIFO 挂起任务支持部分处理，剩余数量保持 pending，直至全部处理。

六、应用侧动态变化注意事项
- allocated_by 用于记录来源流程（如 purchase_checkin:PO...、fifo_manual_match:PO...），并驱动到货一览与账单候选筛选。
- jan_snapshot / item_name_snapshot 为历史快照字段，商品主数据变更不会回写历史单据。
- 超管可通过 db/table/* 通用接口直接改表，但需遵守业务状态机，避免数据不一致。