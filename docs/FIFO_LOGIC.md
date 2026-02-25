# FIFO 业务逻辑说明（当前实现）

本文档描述 SFE 项目中“进货单盘点完成后”的 FIFO 分配与挂起规则。

## 1. 触发点

在超级管理员「进货单管理」页面，点击某进货单的【盘点完成】按钮：

- 接口：`POST /api/purchase-orders/{po_id}/status`
- 入参：`{ status: "checked_inbound" }`

## 2. 处理对象

按该进货单下的每一条进货明细（`purchase_order_lines`）逐行处理，核心字段：

- `JAN`
- `品名`
- `数量`
- `进货单价`

## 3. 货品与订单的区分

- **货品（到货）**：来自进货单明细（`purchase_order_lines`）
- **订单（需求）**：来自客户订单（`customer_orders`）

FIFO 的本质是：将“到货货品”按规则匹配到“客户订单需求”。

## 4. FIFO 判定规则（当前）

对每条进货明细先按 JAN 找到商品（`items`），再找该商品下未完成订单（`status=open`）。

### 4.1 多客户命中（优先拦截）

若同一 JAN 命中 **2 个及以上客户** 的未完成订单：

- 立即取消自动分配
- 不自动入库分配到订单
- 生成挂起任务到 `fifo_pending_tasks`
  - `reason_code = multi_customer_match`
  - `reason_text = JAN命中多个客户未完成订单，需人工干预`

### 4.2 无匹配

若同一 JAN 命中 **0 个**未完成订单：

- 不自动分配
- 生成挂起任务到 `fifo_pending_tasks`
  - `reason_code = no_order_match`
  - `reason_text = 未命中客户订单，需人工处理`

### 4.3 单客户命中（自动执行）

若同一 JAN 仅命中 **1 个客户** 的未完成订单：

- 自动入库生成库存批次（`inventory_lots`）
- 自动按订单创建时间升序进行分配（FIFO）
- 生成分配记录（`allocations`）
- 更新订单已分配数量与状态（`open/closed`）

## 5. FIFO 管理页结构

页面：超级管理员 → FIFO管理

分为两块：

1. **多客户命中分配管理**
2. **无匹配货品管理**

两块表格统一展示列：

- 进货单号
- 进货日期
- JAN
- 品名
- 数量
- 进货价格
- 操作

## 6. 防重复策略

生成挂起任务时，系统会检查同一进货明细在同一原因下是否已有 `pending` 任务：

- 若已存在，不重复插入
- 避免重复盘点导致挂起任务无限叠加

## 7. 相关数据表

- `purchase_orders`
- `purchase_order_lines`
- `items`
- `customer_orders`
- `inventory_lots`
- `allocations`
- `fifo_pending_tasks`

## 8. 备注

- 当前规则：多客户命中与无匹配均进入 FIFO 人工干预；仅单客户命中自动分配。
- 该文档对应实现提交时间：2026-02-25。
