# SFE 数据库说明（自动生成）

- 生成时间: 2026-02-26 04:04:39
- 数据库文件: `C:\sfe-system\sfe.db`

## 1) 表清单与业务定位
- `allocations`: 分配记录（订单行 x 批次 x 客户）
- `auth_tokens`: 登录令牌，绑定用户会话
- `bill_lines`: 账单行（来自allocation，记录售价和行金额）
- `bills`: 账单头（金额、支付与物流状态）
- `customer_orders`: 客户下单明细（需求数量、已分配数量、状态）
- `customers`: 客户主数据（客户名称、启用状态）
- `fifo_pending_tasks`: FIFO待处理任务（多客户命中/无订单命中等）
- `inventory_lots`: 库存批次（入库量、剩余量、FIFO顺序）
- `items`: 商品主数据（JAN、品牌、品名、规格、标价）
- `purchase_order_lines`: 进货单行（JAN、数量、进货单价）
- `purchase_orders`: 进货单头（供应商、状态、成本、付款状态）
- `suppliers`: 供应商主数据
- `users`: 系统账号（super_admin/admin/customer）及客户账号归属

## 2) 各表字段说明
### `allocations`

| 字段 | 类型 | 非空 | 主键 | 默认值 | 说明 |
|---|---|---|---|---|---|
| `id` | `INTEGER` | Y | Y | `` |  |
| `customer_id` | `INTEGER` | Y | N | `` | 外键/关联键 |
| `order_line_id` | `INTEGER` | Y | N | `` | 外键/关联键 |
| `lot_id` | `INTEGER` | Y | N | `` | 外键/关联键 |
| `item_id` | `INTEGER` | Y | N | `` | 外键/关联键 |
| `qty_allocated` | `INTEGER` | Y | N | `` | 数量字段 |
| `fifo_rank_snapshot` | `INTEGER` | Y | N | `` |  |
| `status` | `VARCHAR(16)` | Y | N | `` | 状态字段 |
| `allocated_by` | `VARCHAR(64)` | Y | N | `` |  |
| `created_at` | `DATETIME` | Y | N | `` | 时间戳 |

外键关系:
- `allocations.item_id` -> `items.id`
- `allocations.lot_id` -> `inventory_lots.id`
- `allocations.order_line_id` -> `customer_orders.id`
- `allocations.customer_id` -> `customers.id`

### `auth_tokens`

| 字段 | 类型 | 非空 | 主键 | 默认值 | 说明 |
|---|---|---|---|---|---|
| `id` | `INTEGER` | Y | Y | `` |  |
| `token` | `VARCHAR(255)` | Y | N | `` |  |
| `user_id` | `INTEGER` | Y | N | `` | 外键/关联键 |
| `created_at` | `DATETIME` | Y | N | `` | 时间戳 |

外键关系:
- `auth_tokens.user_id` -> `users.id`

### `bill_lines`

| 字段 | 类型 | 非空 | 主键 | 默认值 | 说明 |
|---|---|---|---|---|---|
| `id` | `INTEGER` | Y | Y | `` |  |
| `bill_id` | `INTEGER` | Y | N | `` | 外键/关联键 |
| `allocation_id` | `INTEGER` | Y | N | `` | 外键/关联键 |
| `item_id` | `INTEGER` | Y | N | `` | 外键/关联键 |
| `jan_snapshot` | `VARCHAR(64)` | Y | N | `` |  |
| `item_name_snapshot` | `VARCHAR(255)` | Y | N | `` |  |
| `qty` | `INTEGER` | Y | N | `` | 数量字段 |
| `sale_unit_price` | `FLOAT` | Y | N | `` | 金额字段 |
| `line_amount` | `FLOAT` | Y | N | `` | 金额字段 |
| `created_at` | `DATETIME` | Y | N | `` | 时间戳 |

外键关系:
- `bill_lines.item_id` -> `items.id`
- `bill_lines.allocation_id` -> `allocations.id`
- `bill_lines.bill_id` -> `bills.id`

### `bills`

| 字段 | 类型 | 非空 | 主键 | 默认值 | 说明 |
|---|---|---|---|---|---|
| `id` | `INTEGER` | Y | Y | `` |  |
| `customer_id` | `INTEGER` | Y | N | `` | 外键/关联键 |
| `bill_no` | `VARCHAR(32)` | Y | N | `` |  |
| `status` | `VARCHAR(16)` | Y | N | `` | 状态字段 |
| `payment_status` | `VARCHAR(16)` | Y | N | `` | 状态字段 |
| `shipping_status` | `VARCHAR(16)` | Y | N | `` | 状态字段 |
| `total_amount` | `FLOAT` | Y | N | `` | 金额字段 |
| `currency` | `VARCHAR(8)` | Y | N | `` |  |
| `payment_confirmed_at` | `DATETIME` | N | N | `` | 时间戳 |
| `created_at` | `DATETIME` | Y | N | `` | 时间戳 |
| `archived_at` | `DATETIME` | N | N | `` | 时间戳 |

外键关系:
- `bills.customer_id` -> `customers.id`

### `customer_orders`

| 字段 | 类型 | 非空 | 主键 | 默认值 | 说明 |
|---|---|---|---|---|---|
| `id` | `INTEGER` | Y | Y | `` |  |
| `customer_id` | `INTEGER` | Y | N | `` | 外键/关联键 |
| `item_id` | `INTEGER` | Y | N | `` | 外键/关联键 |
| `jan_snapshot` | `VARCHAR(64)` | Y | N | `` |  |
| `item_name_snapshot` | `VARCHAR(255)` | Y | N | `` |  |
| `qty_requested` | `INTEGER` | Y | N | `` | 数量字段 |
| `qty_allocated` | `INTEGER` | Y | N | `` | 数量字段 |
| `status` | `VARCHAR(16)` | Y | N | `` | 状态字段 |
| `created_at` | `DATETIME` | Y | N | `` | 时间戳 |

外键关系:
- `customer_orders.item_id` -> `items.id`
- `customer_orders.customer_id` -> `customers.id`

### `customers`

| 字段 | 类型 | 非空 | 主键 | 默认值 | 说明 |
|---|---|---|---|---|---|
| `id` | `INTEGER` | Y | Y | `` |  |
| `name` | `VARCHAR(100)` | Y | N | `` |  |
| `phone` | `VARCHAR(50)` | N | N | `` |  |
| `email` | `VARCHAR(100)` | N | N | `` |  |
| `note` | `VARCHAR(255)` | N | N | `` |  |
| `created_at` | `DATETIME` | N | N | `` | 时间戳 |
| `is_active` | `BOOLEAN` | N | N | `1` |  |

### `fifo_pending_tasks`

| 字段 | 类型 | 非空 | 主键 | 默认值 | 说明 |
|---|---|---|---|---|---|
| `id` | `INTEGER` | Y | Y | `` |  |
| `purchase_order_line_id` | `INTEGER` | N | N | `` | 外键/关联键 |
| `source_po_no` | `VARCHAR(64)` | Y | N | `` |  |
| `jan` | `VARCHAR(64)` | Y | N | `` |  |
| `item_name` | `VARCHAR(255)` | N | N | `` |  |
| `qty` | `INTEGER` | Y | N | `` | 数量字段 |
| `reason_code` | `VARCHAR(64)` | Y | N | `` |  |
| `reason_text` | `TEXT` | Y | N | `` |  |
| `status` | `VARCHAR(16)` | Y | N | `` | 状态字段 |
| `resolution_note` | `TEXT` | N | N | `` |  |
| `resolved_by` | `VARCHAR(64)` | N | N | `` |  |
| `resolved_at` | `DATETIME` | N | N | `` | 时间戳 |
| `created_at` | `DATETIME` | Y | N | `` | 时间戳 |

外键关系:
- `fifo_pending_tasks.purchase_order_line_id` -> `purchase_order_lines.id`

### `inventory_lots`

| 字段 | 类型 | 非空 | 主键 | 默认值 | 说明 |
|---|---|---|---|---|---|
| `id` | `INTEGER` | Y | Y | `` |  |
| `item_id` | `INTEGER` | Y | N | `` | 外键/关联键 |
| `qty_received` | `INTEGER` | Y | N | `` | 数量字段 |
| `qty_remaining` | `INTEGER` | Y | N | `` | 数量字段 |
| `fifo_rank` | `INTEGER` | Y | N | `` |  |
| `location` | `VARCHAR(128)` | N | N | `` |  |
| `created_at` | `DATETIME` | Y | N | `` | 时间戳 |

外键关系:
- `inventory_lots.item_id` -> `items.id`

### `items`

| 字段 | 类型 | 非空 | 主键 | 默认值 | 说明 |
|---|---|---|---|---|---|
| `id` | `INTEGER` | Y | Y | `` |  |
| `jan` | `VARCHAR(64)` | Y | N | `` |  |
| `brand` | `VARCHAR(128)` | Y | N | `` |  |
| `name` | `VARCHAR(255)` | Y | N | `` |  |
| `spec` | `VARCHAR(255)` | N | N | `` |  |
| `msrp_price` | `FLOAT` | Y | N | `` | 金额字段 |
| `in_qty` | `INTEGER` | Y | N | `` |  |
| `is_active` | `BOOLEAN` | Y | N | `` |  |
| `created_at` | `DATETIME` | Y | N | `` | 时间戳 |

### `purchase_order_lines`

| 字段 | 类型 | 非空 | 主键 | 默认值 | 说明 |
|---|---|---|---|---|---|
| `id` | `INTEGER` | Y | Y | `` |  |
| `purchase_order_id` | `INTEGER` | Y | N | `` | 外键/关联键 |
| `jan` | `VARCHAR(64)` | Y | N | `` |  |
| `item_name_snapshot` | `VARCHAR(255)` | Y | N | `` |  |
| `qty` | `INTEGER` | Y | N | `` | 数量字段 |
| `unit_cost` | `FLOAT` | Y | N | `` | 金额字段 |
| `line_total` | `FLOAT` | Y | N | `` | 金额字段 |
| `created_at` | `DATETIME` | Y | N | `` | 时间戳 |

外键关系:
- `purchase_order_lines.purchase_order_id` -> `purchase_orders.id`

### `purchase_orders`

| 字段 | 类型 | 非空 | 主键 | 默认值 | 说明 |
|---|---|---|---|---|---|
| `id` | `INTEGER` | Y | Y | `` |  |
| `po_no` | `VARCHAR(64)` | Y | N | `` |  |
| `supplier_id` | `INTEGER` | Y | N | `` | 外键/关联键 |
| `payment_status` | `VARCHAR(16)` | Y | N | `` | 状态字段 |
| `status` | `VARCHAR(32)` | Y | N | `` | 状态字段 |
| `total_cost` | `FLOAT` | Y | N | `` | 金额字段 |
| `purchased_at` | `DATETIME` | Y | N | `` | 时间戳 |
| `created_at` | `DATETIME` | Y | N | `` | 时间戳 |

外键关系:
- `purchase_orders.supplier_id` -> `suppliers.id`

### `suppliers`

| 字段 | 类型 | 非空 | 主键 | 默认值 | 说明 |
|---|---|---|---|---|---|
| `id` | `INTEGER` | Y | Y | `` |  |
| `supplier_code` | `VARCHAR(64)` | Y | N | `` |  |
| `name` | `VARCHAR(128)` | Y | N | `` |  |
| `is_active` | `BOOLEAN` | Y | N | `` |  |
| `created_at` | `DATETIME` | Y | N | `` | 时间戳 |

### `users`

| 字段 | 类型 | 非空 | 主键 | 默认值 | 说明 |
|---|---|---|---|---|---|
| `id` | `INTEGER` | Y | Y | `` |  |
| `username` | `VARCHAR(64)` | Y | N | `` |  |
| `password` | `VARCHAR(128)` | Y | N | `` |  |
| `role` | `VARCHAR(32)` | Y | N | `` |  |
| `customer_id` | `INTEGER` | N | N | `` | 外键/关联键 |
| `created_at` | `DATETIME` | Y | N | `` | 时间戳 |
| `is_active` | `BOOLEAN` | N | N | `1` |  |

外键关系:
- `users.customer_id` -> `customers.id`

## 3) 关联关系总览
- `allocations.item_id` -> `items.id`
- `allocations.lot_id` -> `inventory_lots.id`
- `allocations.order_line_id` -> `customer_orders.id`
- `allocations.customer_id` -> `customers.id`
- `auth_tokens.user_id` -> `users.id`
- `bill_lines.item_id` -> `items.id`
- `bill_lines.allocation_id` -> `allocations.id`
- `bill_lines.bill_id` -> `bills.id`
- `bills.customer_id` -> `customers.id`
- `customer_orders.item_id` -> `items.id`
- `customer_orders.customer_id` -> `customers.id`
- `fifo_pending_tasks.purchase_order_line_id` -> `purchase_order_lines.id`
- `inventory_lots.item_id` -> `items.id`
- `purchase_order_lines.purchase_order_id` -> `purchase_orders.id`
- `purchase_orders.supplier_id` -> `suppliers.id`
- `users.customer_id` -> `customers.id`

## 4) 核心业务动作与数据反应
- **导入/新增进货单**：创建 purchase_orders + purchase_order_lines，状态初始 created_unchecked
- **进货单盘点入库**：按JAN匹配开放订单；单客户自动分配，多客户/无匹配生成 fifo_pending_tasks
- **FIFO人工处理**：在 fifo_pending_tasks 上执行匹配订单/转无匹配/指定客户，写入 allocations + inventory_lots
- **客户下单**：写入 customer_orders，等待分配
- **生成账单（到货一览）**：使用 active allocations 生成 bills + bill_lines，并将 allocation 置为 billed
- **账单状态推进**：按角色和状态机推进到 archived；客户仅可执行 pay/confirm_receipt
- **删除保护**：有外键引用时拒绝删除，避免脏数据；已盘点明细禁止删除

## 5) 状态流与变动说明
- `purchase_orders.status`: created_unchecked -> checked_inbound（不可逆）
- `purchase_orders.payment_status`: unpaid -> paid
- `customer_orders.status`: open -> closed
- `allocations.status`: active -> billed
- `bills.stage`: created -> paid -> confirmed -> shipped -> received -> archived
- `fifo_pending_tasks.status`: pending -> resolved
- 进货单 `checked_inbound` 后不可回退。
- 账单生成后，关联 allocation 从 `active` 变为 `billed`，避免重复开票。
- FIFO 挂起任务支持部分处理；剩余数量继续保留在 pending。

## 6) 应用侧动态变化注意事项
- `allocated_by` 记录来源流程（如 `purchase_checkin:PO...`、`fifo_manual_match:PO...`），用于到货/账单候选筛选。
- `jan_snapshot` / `item_name_snapshot` 用于冻结历史快照，避免商品主数据变更影响历史单据。
- `db/table/*` 通用接口支持超管直接改表，需注意和业务状态机一致性。