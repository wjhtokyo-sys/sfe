# SFE System

## 已完成内容
- 后端：FastAPI + SQLAlchemy，完成 订单→到货→FIFO分配→账单→状态推进 闭环
- 前端：React + Ant Design + Redux Toolkit 可视化看板
- 测试：pytest 覆盖核心闭环

## 启动方式
### 1) 后端
```bash
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn main:app --reload
```

### 2) 前端
```bash
cd frontend
npm install
npm run dev
```

## 业务规范文档
- Database ER Diagram: [`docs/DATABASE_ER.md`](docs/DATABASE_ER.md)
- Business & Data Spec (Final): [`docs/BUSINESS_DATA_SPEC.md`](docs/BUSINESS_DATA_SPEC.md)
- 操作轨迹报告（简版）: [`docs/OPERATION_TRACE.md`](docs/OPERATION_TRACE.md)
