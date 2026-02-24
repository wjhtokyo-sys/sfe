import React, { useEffect, useMemo, useState } from 'react';
import {
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Layout,
  Menu,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { api } from './api/client';

const { Sider, Content } = Layout;
const { Title } = Typography;

export default function App() {
  const [mode, setMode] = useState('home');
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [role, setRole] = useState(localStorage.getItem('role') || '');
  const [menu, setMenu] = useState('items');
  const [me, setMe] = useState(null);
  const [loading, setLoading] = useState(false);
  const [orderModal, setOrderModal] = useState({ open: false, item: null });
  const [orderQty, setOrderQty] = useState(1);

  const [data, setData] = useState({ items: [], orders: [], bills: [], customers: [], lots: [], allocations: [] });

  const authHeaders = useMemo(() => ({ headers: { Authorization: `Bearer ${token}` } }), [token]);

  const login = async (url, values) => {
    try {
      const res = await api.post(url, values);
      setToken(res.data.token);
      setRole(res.data.role);
      setMode('panel');
      localStorage.setItem('token', res.data.token);
      localStorage.setItem('role', res.data.role);
      message.success('登录成功');
    } catch (err) {
      message.error(err?.response?.data?.detail || '登录失败');
    }
  };

  const logout = () => {
    setToken('');
    setRole('');
    setMode('home');
    setMenu('items');
    setMe(null);
    localStorage.clear();
    message.success('已登出');
  };

  const req = (u) => api.get(u, authHeaders).then((r) => r.data).catch(() => []);

  const load = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const profile = await api.get('/auth/me', authHeaders).then((r) => r.data);
      setMe(profile);
      const [items, orders, bills, customers, lots, allocations] = await Promise.all([
        req('/api/items'),
        req('/api/orders'),
        req('/api/bills'),
        req('/api/customers'),
        req('/api/lots'),
        req('/api/allocations'),
      ]);
      setData({ items, orders, bills, customers, lots, allocations });
    } catch {
      message.error('会话失效，请重新登录');
      logout();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      setMode('panel');
      load();
    }
  }, [token]);

  const createOrderByCustomer = async () => {
    if (!orderModal.item || !me?.customer_id) return;
    if (orderQty <= 0) return message.error('订货数必须大于0');
    await api.post('/api/orders', { customer_id: me.customer_id, item_id: orderModal.item.id, qty_requested: orderQty }, authHeaders);
    message.success('下单成功');
    setOrderModal({ open: false, item: null });
    setOrderQty(1);
    load();
  };

  const doAdminAction = async (fn) => {
    try {
      await fn();
      message.success('操作成功');
      load();
    } catch (e) {
      message.error(e?.response?.data?.detail || '操作失败');
    }
  };

  if (mode === 'home') {
    return (
      <div className="page">
        <Title level={3}>SFE 登录入口</Title>
        <div className="login-wrap">
          <Card title="客户登录入口页">
            <Form onFinish={(v) => login('/auth/customer-login', v)}>
              <Form.Item name="username" rules={[{ required: true }]}><Input placeholder="客户账号" /></Form.Item>
              <Form.Item name="password" rules={[{ required: true }]}><Input.Password placeholder="密码" /></Form.Item>
              <Button className="click-btn" type="primary" htmlType="submit">客户登录</Button>
            </Form>
          </Card>
        </div>
        <div className="login-wrap">
          <Card title="管理员登录入口页">
            <Form onFinish={(v) => login('/auth/admin-login', v)}>
              <Form.Item name="username" rules={[{ required: true }]}><Input placeholder="管理员账号" /></Form.Item>
              <Form.Item name="password" rules={[{ required: true }]}><Input.Password placeholder="密码" /></Form.Item>
              <Button className="click-btn" type="primary" htmlType="submit">管理员登录</Button>
            </Form>
          </Card>
        </div>
      </div>
    );
  }

  const customerMenus = [
    { key: 'items', label: '商品信息查询' },
    { key: 'orders', label: '订单管理' },
    { key: 'bills', label: '账单管理' },
    { key: 'history', label: '历史账单' },
  ];

  const adminMenus = [
    { key: 'customers', label: '客户管理' },
    { key: 'fifo', label: 'FIFO管理' },
    { key: 'orders', label: '订单管理' },
    { key: 'bills', label: '账单管理' },
    { key: 'history', label: '历史账单管理' },
  ];

  const customerItemColumns = [
    { title: 'JAN', dataIndex: 'jan' },
    { title: '品牌', dataIndex: 'brand' },
    { title: '名称', dataIndex: 'name' },
    { title: '建议价', dataIndex: 'msrp_price' },
    {
      title: '操作',
      render: (_, row) => <Button className="click-btn" type="primary" onClick={() => setOrderModal({ open: true, item: row })}>下单</Button>,
    },
  ];

  const orderColumns = [
    { title: '订单ID', dataIndex: 'id' },
    { title: '商品', dataIndex: 'item_name_snapshot' },
    { title: '订货数', dataIndex: 'qty_requested' },
    { title: '已分配', dataIndex: 'qty_allocated' },
    { title: '状态', dataIndex: 'status', render: (v) => <Tag>{v}</Tag> },
  ];

  const billColumns = [
    { title: '账单号', dataIndex: 'bill_no' },
    { title: '金额', dataIndex: 'total_amount' },
    { title: '账单状态', dataIndex: 'status', render: (v) => <Tag>{v}</Tag> },
    { title: '付款状态', dataIndex: 'payment_status', render: (v) => <Tag>{v}</Tag> },
    { title: '物流状态', dataIndex: 'shipping_status', render: (v) => <Tag>{v}</Tag> },
  ];

  const adminOrderColumns = [...orderColumns, { title: '客户ID', dataIndex: 'customer_id' }];
  const adminCustomerColumns = [{ title: '客户ID', dataIndex: 'id' }, { title: '名称', dataIndex: 'name' }];
  const lotColumns = [{ title: '批次ID', dataIndex: 'id' }, { title: '商品ID', dataIndex: 'item_id' }, { title: '剩余', dataIndex: 'qty_remaining' }, { title: 'FIFO序', dataIndex: 'fifo_rank' }];
  const allocColumns = [{ title: '分配ID', dataIndex: 'id' }, { title: '订单ID', dataIndex: 'order_line_id' }, { title: '批次ID', dataIndex: 'lot_id' }, { title: '数量', dataIndex: 'qty_allocated' }, { title: '状态', dataIndex: 'status' }];

  const AdminOrdersPanel = () => {
    const [f, setF] = useState({ customer_id: undefined, item_id: undefined, qty_requested: 1 });
    return <Card className="panel" title="订单管理">
      <Space wrap>
        <Select style={{ width: 160 }} placeholder="客户" options={data.customers.map(c=>({label:`${c.id}-${c.name}`,value:c.id}))} onChange={(v)=>setF({...f,customer_id:v})} />
        <Select style={{ width: 220 }} placeholder="商品" options={data.items.map(i=>({label:`${i.jan}-${i.name}`,value:i.id}))} onChange={(v)=>setF({...f,item_id:v})} />
        <InputNumber min={1} value={f.qty_requested} onChange={(v)=>setF({...f,qty_requested:v||1})} />
        <Button className="click-btn" type="primary" onClick={()=>doAdminAction(()=>api.post('/api/orders',f,authHeaders))}>新增订单</Button>
      </Space>
      <Table rowKey="id" columns={adminOrderColumns} dataSource={data.orders} loading={loading} style={{ marginTop: 12 }} />
    </Card>;
  };

  const AdminFifoPanel = () => {
    const [lot, setLot] = useState({ item_id: undefined, qty_received: 1 });
    const [orderLineId, setOrderLineId] = useState();
    return <Card className="panel" title="FIFO管理">
      <Space wrap>
        <Select style={{ width: 220 }} placeholder="商品" options={data.items.map(i=>({label:`${i.jan}-${i.name}`,value:i.id}))} onChange={(v)=>setLot({...lot,item_id:v})} />
        <InputNumber min={1} value={lot.qty_received} onChange={(v)=>setLot({...lot,qty_received:v||1})} />
        <Button className="click-btn" type="primary" onClick={()=>doAdminAction(()=>api.post('/api/lots',lot,authHeaders))}>到货入库</Button>
        <Select style={{ width: 220 }} placeholder="待分配订单" options={data.orders.filter(o=>o.status==='open').map(o=>({label:`订单${o.id} ${o.item_name_snapshot}`,value:o.id}))} onChange={setOrderLineId} />
        <Button className="click-btn" onClick={()=>doAdminAction(()=>api.post('/api/allocations/fifo',{order_line_id:orderLineId,allocated_by:role},authHeaders))}>执行FIFO分配</Button>
      </Space>
      <Table rowKey="id" columns={lotColumns} dataSource={data.lots} style={{ marginTop: 12 }} />
      <Table rowKey="id" columns={allocColumns} dataSource={data.allocations} style={{ marginTop: 12 }} />
    </Card>;
  };

  const AdminBillsPanel = () => {
    const [billForm, setBillForm] = useState({ customer_id: undefined, allocation_ids: '', sale_unit_price: 1 });
    const [stateForm, setStateForm] = useState({ bill_id: undefined, action: 'pay' });
    return <Card className="panel" title="账单管理">
      <Space wrap>
        <Select style={{ width: 180 }} placeholder="客户" options={data.customers.map(c=>({label:`${c.id}-${c.name}`,value:c.id}))} onChange={(v)=>setBillForm({...billForm,customer_id:v})} />
        <Input style={{ width: 220 }} placeholder="allocation ids: 1,2" onChange={(e)=>setBillForm({...billForm,allocation_ids:e.target.value})} />
        <InputNumber min={1} value={billForm.sale_unit_price} onChange={(v)=>setBillForm({...billForm,sale_unit_price:v||1})} />
        <Button className="click-btn" type="primary" onClick={()=>doAdminAction(()=>api.post('/api/bills',{...billForm,allocation_ids:billForm.allocation_ids.split(',').map(s=>Number(s.trim())).filter(Boolean)},authHeaders))}>生成账单</Button>
      </Space>
      <Space wrap style={{ marginTop: 8 }}>
        <Select style={{ width: 180 }} placeholder="账单" options={data.bills.map(b=>({label:`${b.id}-${b.bill_no}`,value:b.id}))} onChange={(v)=>setStateForm({...stateForm,bill_id:v})} />
        <Select style={{ width: 180 }} value={stateForm.action} onChange={(v)=>setStateForm({...stateForm,action:v})}
          options={['pay','confirm_receipt','ship','deliver','archive'].map(v=>({label:v,value:v}))} />
        <Popconfirm title="确认推进状态？" onConfirm={()=>doAdminAction(()=>api.post(`/api/bills/${stateForm.bill_id}/state`,{action:stateForm.action},authHeaders))}>
          <Button className="click-btn">状态推进</Button>
        </Popconfirm>
      </Space>
      <Table rowKey="id" columns={billColumns} dataSource={data.bills} style={{ marginTop: 12 }} />
    </Card>;
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider>
        <div style={{ color: '#fff', padding: 16 }}>{role === 'customer' ? '客户管理页' : '管理员管理页'}</div>
        <Menu theme="dark" mode="inline" selectedKeys={[menu]} items={role === 'customer' ? customerMenus : adminMenus} onClick={(e) => setMenu(e.key)} />
      </Sider>
      <Layout>
        <Content className="page">
          <Space>
            <Button className="click-btn" onClick={load}>刷新</Button>
            <Button className="click-btn" danger onClick={logout}>登出</Button>
          </Space>

          {role === 'customer' && menu === 'items' && <Card className="panel" title="商品信息查询"><Table rowKey="id" columns={customerItemColumns} dataSource={data.items} loading={loading} /></Card>}
          {role === 'customer' && menu === 'orders' && <Card className="panel" title="订单管理"><Table rowKey="id" columns={orderColumns} dataSource={data.orders} /></Card>}
          {role === 'customer' && menu === 'bills' && <Card className="panel" title="账单管理"><Table rowKey="id" columns={billColumns} dataSource={data.bills} /></Card>}
          {role === 'customer' && menu === 'history' && <Card className="panel" title="历史账单"><Table rowKey="id" columns={billColumns} dataSource={data.bills.filter((b) => b.status === 'archived')} /></Card>}

          {role !== 'customer' && menu === 'customers' && <Card className="panel" title="客户管理"><Table rowKey="id" columns={adminCustomerColumns} dataSource={data.customers} /></Card>}
          {role !== 'customer' && menu === 'fifo' && <AdminFifoPanel />}
          {role !== 'customer' && menu === 'orders' && <AdminOrdersPanel />}
          {role !== 'customer' && menu === 'bills' && <AdminBillsPanel />}
          {role !== 'customer' && menu === 'history' && <Card className="panel" title="历史账单管理"><Table rowKey="id" columns={billColumns} dataSource={data.bills.filter((b) => b.status === 'archived')} /></Card>}

          <Modal title={`下单：${orderModal.item?.name || ''}`} open={orderModal.open} onCancel={() => setOrderModal({ open: false, item: null })} onOk={createOrderByCustomer} okText="确认下单">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>客户：{me?.username}</div>
              <InputNumber min={1} value={orderQty} onChange={(v) => setOrderQty(v || 1)} style={{ width: '100%' }} />
            </Space>
          </Modal>
        </Content>
      </Layout>
    </Layout>
  );
}
