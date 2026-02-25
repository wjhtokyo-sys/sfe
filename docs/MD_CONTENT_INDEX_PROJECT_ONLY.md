# SFE 项目 Markdown 内容清单（项目文件）

统计时间：2026-02-26 04:21:00 (Asia/Tokyo)
总计：11 个 MD 文件（已排除 .venv / venv / node_modules / .git / .pytest_cache）

- `docs/BUSINESS_DATA_SPEC.md`
  - 标题/首行：SFE 业务与数据结构统一规范（最终版）
  - 内容摘要：> 本文档为 SFE 项目唯一业务语义与流程约束说明。 | > 目标：统一概念、消除歧义、固化流程与状态守卫，作为后续开发与审计基线。
- `docs/DATABASE_ER.md`
  - 标题/首行：SFE Database ER Diagram
  - 内容摘要：![SFE Database ER Diagram - Latest](./images/SFE_ER_LATEST.jpg) | Generated from current project tables and FK relations.
- `docs/FIFO_LOGIC.md`
  - 标题/首行：FIFO 业务逻辑说明（当前实现）
  - 内容摘要：本文档描述 SFE 项目中“进货单盘点完成后”的 FIFO 分配与挂起规则。 | 在超级管理员「进货单管理」页面，点击某进货单的【盘点完成】按钮：
- `docs/MD_CONTENT_INDEX.md`
  - 标题/首行：SFE 项目 Markdown 内容清单
  - 内容摘要：统计时间：2026-02-26 04:20:40 (Asia/Tokyo) | 总计：274 个 MD 文件
- `docs/OPERATION_MANUAL.md`
  - 标题/首行：SFE 操作手册（非IT版）
  - 内容摘要：1. 打开 VS Code 终端，进入 `C:\sfe-system` | 2. 运行后端：
- `docs/OPERATION_TRACE.md`
  - 标题/首行：SFE 操作轨迹报告（简版，非技术版）
  - 内容摘要：我已按你的业务框架，做出一套可以跑通的“后端+前端”最小闭环系统： | - 客户下单（订单）
- `docs/OPTIMIZATION_REFERENCE.md`
  - 标题/首行：SFE 优化参考（仅方案评估，不改代码与数据）
  - 内容摘要：> 目标：在**完全保证现有功能**前提下，对 SFE 的业务链路与数据组织进行压缩与简化，供后续迭代参考。 | > 范围：本文件仅为优化参考，不包含任何实施改动。
- `docs/PROJECT_CONFIG.md`
  - 标题/首行：SFE 项目配置
  - 内容摘要：- 系统默认币种：`JPY` | - 显示货币：日元（円）
- `docs/SFE_DATABASE_SPEC.md`
  - 标题/首行：SFE 数据库说明（自动生成）
  - 内容摘要：- 生成时间: 2026-02-26 04:04:39 | - 数据库文件: `C:\sfe-system\sfe.db`
- `docs/SFE_DATABASE_SPEC_TEXT.md`
  - 标题/首行：SFE 数据库说明（纯文本版，可直接复制）
  - 内容摘要：生成时间：2026-02-26 04:10:48 | 数据库文件：C:\sfe-system\sfe.db
- `README.md`
  - 标题/首行：SFE System
  - 内容摘要：- 后端：FastAPI + SQLAlchemy，完成 订单→到货→FIFO分配→账单→状态推进 闭环 | - 前端：React + Ant Design + Redux Toolkit 可视化看板