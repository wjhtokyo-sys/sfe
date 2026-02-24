import React, { useEffect, useMemo, useState } from 'react';
import { Button, Card, Form, Input, InputNumber, Layout, Menu, Modal, Popconfirm, Select, Space, Switch, Table, Tag, Typography, Upload, message } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { api } from './api/client';

const { Sider, Content } = Layout;
const { Title } = Typography;

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [role, setRole] = useState(localStorage.getItem('role') || '');
  const [menu, setMenu] = useState('items');
  const [me, setMe] = useState(null);
  const [kw, setKw] = useState('');
  const [data, setData] = useState({ items: [], orders: [], bills: [], customers: [], lots: [], allocations: [], superCustomers: [] });
  const [orderPick, setOrderPick] = useState([]);
  const [fifoLot, setFifoLot] = useState({ item_id: undefined, qty_received: 1 });
  const [fifoOrderId, setFifoOrderId] = useState();
  const [orderCustomerFilter, setOrderCustomerFilter] = useState();

  const authHeaders = useMemo(() => ({ headers: { Authorization: `Bearer ${token}` } }), [token]);

  const login = async (url, v) => {
    try {
      const r = await api.post(url, v);
      localStorage.setItem('token', r.data.token);
      localStorage.setItem('role', r.data.role);
      setToken(r.data.token); setRole(r.data.role);
      message.success('登录成功');
    } catch (e) { message.error(e?.response?.data?.detail || '登录失败'); }
  };

  const logout = () => { localStorage.clear(); setToken(''); setRole(''); setMe(null); };

  const load = async () => {
    if (!token) return;
    const meInfo = await api.get('/auth/me', authHeaders).then(r => r.data);
    setMe(meInfo);
    const req = (u) => api.get(u, authHeaders).then(r => r.data).catch(() => []);
    const [items, orders, bills, customers, lots, allocations, superCustomers] = await Promise.all([
      req(`/api/items${kw ? `?keyword=${encodeURIComponent(kw)}` : ''}`),
      req('/api/orders'), req('/api/bills'), req('/api/customers'), req('/api/lots'), req('/api/allocations'), req('/api/super/customers'),
    ]);
    setData({ items, orders, bills, customers, lots, allocations, superCustomers });
  };

  useEffect(() => { if (token) load(); }, [token]);

  useEffect(() => {
    if (!token) return;
    if (role === 'super_admin') setMenu('items_admin');
    if (role === 'customer') setMenu('items');
  }, [token, role]);

  if (!token) return <div className='page'>
    <Title level={3}>SFE 登录入口</Title>
    <Card title='客户登录入口页' className='login-wrap'><Form onFinish={(v) => login('/auth/customer-login', v)}><Form.Item name='username' rules={[{ required: true }]}><Input placeholder='客户账号' /></Form.Item><Form.Item name='password' rules={[{ required: true }]}><Input.Password placeholder='密码' /></Form.Item><Button className='click-btn' htmlType='submit' type='primary'>客户登录</Button></Form></Card>
    <Card title='管理员登录入口页' className='login-wrap'><Form onFinish={(v) => login('/auth/admin-login', v)}><Form.Item name='username' rules={[{ required: true }]}><Input placeholder='管理员账号' /></Form.Item><Form.Item name='password' rules={[{ required: true }]}><Input.Password placeholder='密码' /></Form.Item><Button className='click-btn' htmlType='submit' type='primary'>管理员登录</Button></Form></Card>
  </div>;

  const customerMenus = [{ key: 'items', label: '商品信息查询' }, { key: 'orders', label: '订单管理' }, { key: 'bills', label: '账单管理' }, { key: 'history', label: '历史账单' }];
  const adminMenus = [{ key: 'customers', label: '客户管理' }, { key: 'items_admin', label: '商品信息管理' }, { key: 'fifo', label: 'FIFO管理' }, { key: 'orders', label: '客户订单管理' }, { key: 'bills', label: '账单管理' }, { key: 'history', label: '历史账单管理' }];

  const customerItemCols = [
    { title: 'JAN', dataIndex: 'jan' }, { title: '品牌', dataIndex: 'brand' }, { title: '商品名', dataIndex: 'name' }, { title: '零售价', dataIndex: 'msrp_price' }, { title: '入数', dataIndex: 'in_qty' },
    { title: '操作', render: (_, row) => <CustomerOrderBtn row={row} me={me} authHeaders={authHeaders} reload={load} /> },
  ];

  const orderCols = [{ title: '订单ID', dataIndex: 'id' }, { title: role === 'super_admin' ? '客户名' : '客户ID', dataIndex: 'customer_id', render: (v) => role === 'super_admin' ? (data.customers.find(c => c.id === v)?.name || `客户${v}`) : v }, { title: '商品', dataIndex: 'item_name_snapshot' }, { title: '订货', dataIndex: 'qty_requested' }, { title: '已分配', dataIndex: 'qty_allocated' }, ...(role === 'super_admin' ? [{ title: '状态', dataIndex: 'status', render: (v) => <Tag>{v}</Tag> }, { title: '操作', render: (_, r) => <Popconfirm title='确认删除该订单？' onConfirm={async () => { await api.delete(`/api/orders/${r.id}`, authHeaders); message.success('订单已删除'); load(); }}><Button className='click-btn' danger>删除</Button></Popconfirm> }] : [])];

  const billCols = [{ title: '账单号', dataIndex: 'bill_no' }, { title: '金额', dataIndex: 'total_amount' }, { title: '账单状态', dataIndex: 'status' }, { title: '付款状态', dataIndex: 'payment_status' }, { title: '物流状态', dataIndex: 'shipping_status' }];

  return <Layout style={{ minHeight: '100vh' }}>
    <Sider><div style={{ color: '#fff', padding: 16 }}>{role === 'customer' ? '客户管理页' : '超级管理员管理页'}</div><Menu theme='dark' mode='inline' selectedKeys={[menu]} items={role === 'customer' ? customerMenus : adminMenus} onClick={(e) => setMenu(e.key)} /></Sider>
    <Layout><Content className='page'>
      <Space><Button className='click-btn' onClick={load}>刷新</Button><Button className='click-btn' danger onClick={logout}>登出</Button></Space>

      {role === 'customer' && menu === 'items' && <Card className='panel' title='商品信息查询'>
        <Space><Input placeholder='按JAN或关键字检索' value={kw} onChange={(e) => setKw(e.target.value)} /><Button className='click-btn' onClick={load}>搜索</Button></Space>
        <Table rowKey='id' dataSource={data.items} columns={customerItemCols} style={{ marginTop: 8 }} />
      </Card>}

      {menu === 'orders' && <Card className='panel' title={role === 'super_admin' ? '客户订单管理' : '订单管理'}>
        {role === 'super_admin' && <Space style={{ marginBottom: 8 }}>
          <Select
            allowClear
            placeholder='按客户名筛选'
            style={{ width: 220 }}
            value={orderCustomerFilter}
            options={data.customers.map(c => ({ label: c.name, value: c.id }))}
            onChange={setOrderCustomerFilter}
          />
        </Space>}
        <Table rowKey='id' dataSource={role === 'super_admin' && orderCustomerFilter ? data.orders.filter(o => o.customer_id === orderCustomerFilter) : data.orders} columns={orderCols} />
      </Card>}

      {menu === 'bills' && <AdminBills role={role} authHeaders={authHeaders} bills={data.bills} customers={data.customers} allocations={data.allocations} reload={load} />}
      {menu === 'history' && <Card className='panel' title='历史账单'><Table rowKey='id' dataSource={data.bills.filter(b => b.status === 'archived')} columns={billCols} /></Card>}

      {role !== 'customer' && menu === 'customers' && <SuperCustomerPanel rows={data.superCustomers} authHeaders={authHeaders} reload={load} />}

      {role !== 'customer' && menu === 'items_admin' && <ItemAdminPanel items={data.items} kw={kw} setKw={setKw} load={load} authHeaders={authHeaders} />}

      {role !== 'customer' && menu === 'fifo' && <Card className='panel' title='FIFO管理'>
        <Space wrap>
          <Select placeholder='选择商品' style={{ width: 220 }} options={data.items.map(i => ({ label: `${i.jan}-${i.name}`, value: i.id }))} onChange={(v) => setFifoLot({ ...fifoLot, item_id: v })} />
          <InputNumber min={1} value={fifoLot.qty_received} onChange={(v) => setFifoLot({ ...fifoLot, qty_received: v || 1 })} />
          <Button className='click-btn' onClick={async () => { await api.post('/api/lots', fifoLot, authHeaders); message.success('入库成功'); load(); }}>FIFO入库</Button>
          <Select placeholder='待分配订单' style={{ width: 240 }} options={data.orders.filter(o => o.status === 'open').map(o => ({ label: `订单${o.id}-${o.item_name_snapshot}`, value: o.id }))} onChange={setFifoOrderId} />
          <Button className='click-btn' type='primary' onClick={async () => { await api.post('/api/allocations/fifo', { order_line_id: fifoOrderId, allocated_by: 'super_admin' }, authHeaders); message.success('FIFO划拨成功'); load(); }}>执行FIFO划拨</Button>
        </Space>
        <Table style={{ marginTop: 8 }} rowKey='id' dataSource={data.lots.map(l => ({ ...l, item_name: data.items.find(i => i.id === l.item_id)?.name || '' }))} columns={[{ title: '批次ID', dataIndex: 'id' }, { title: '商品名', dataIndex: 'item_name' }, { title: '剩余', dataIndex: 'qty_remaining' }, { title: 'FIFO序', dataIndex: 'fifo_rank' }]} />
      </Card>}

    </Content></Layout>
  </Layout>;
}

function CustomerOrderBtn({ row, me, authHeaders, reload }) {
  const [open, setOpen] = useState(false); const [qty, setQty] = useState(1);
  return <>
    <Button className='click-btn' type='primary' onClick={() => setOpen(true)}>下单</Button>
    <Modal open={open} title='填写订货数' onCancel={() => setOpen(false)} onOk={async () => { await api.post('/api/orders', { customer_id: me.customer_id, item_id: row.id, qty_requested: qty }, authHeaders); message.success('下单成功'); setOpen(false); reload(); }}>
      <InputNumber min={1} value={qty} onChange={(v) => setQty(v || 1)} style={{ width: '100%' }} />
    </Modal>
  </>;
}

function SuperCustomerPanel({ rows, authHeaders, reload }) {
  const [edit, setEdit] = useState(null); const [pwd, setPwd] = useState(''); const [active, setActive] = useState(true);
  const [editUsername, setEditUsername] = useState('');
  const [editCustomerName, setEditCustomerName] = useState('');
  const [newUser, setNewUser] = useState({ username: '', password: '', customer_name: '' });
  const cols = [
    { title: '用户名', dataIndex: 'username' }, { title: '客户名', dataIndex: 'customer_name' }, { title: '激活', dataIndex: 'is_active', render: (v) => <Tag>{v ? '启用' : '停用'}</Tag> },
    { title: '操作', render: (_, r) => <Space><Button className='click-btn' onClick={() => { setEdit(r); setPwd(''); setActive(r.is_active); setEditUsername(r.username || ''); setEditCustomerName(r.customer_name || ''); }}>修改</Button><Popconfirm title='确认删除客户？' onConfirm={async () => { await api.delete(`/api/super/customers/${r.user_id}`, authHeaders); message.success('已删除'); reload(); }}><Button className='click-btn' danger>删除</Button></Popconfirm></Space> },
  ];
  return <Card className='panel' title='客户管理'>
    <Space wrap style={{ marginBottom: 8 }}>
      <Input placeholder='客户登录账号' value={newUser.username} onChange={(e) => setNewUser({ ...newUser, username: e.target.value })} />
      <Input.Password placeholder='客户登录密码' value={newUser.password} onChange={(e) => setNewUser({ ...newUser, password: e.target.value })} />
      <Input placeholder='客户名称' value={newUser.customer_name} onChange={(e) => setNewUser({ ...newUser, customer_name: e.target.value })} />
      <Button className='click-btn' type='primary' onClick={async () => { await api.post('/api/super/customers', newUser, authHeaders); message.success('新增客户成功'); setNewUser({ username: '', password: '', customer_name: '' }); reload(); }}>新增客户</Button>
    </Space>
    <Table rowKey='user_id' columns={cols} dataSource={rows} />
    <Modal open={!!edit} title='修改客户账号' onCancel={() => setEdit(null)} onOk={async () => { await api.patch(`/api/super/customers/${edit.user_id}`, { username: editUsername || undefined, customer_name: editCustomerName || undefined, password: pwd || undefined, is_active: active }, authHeaders); message.success('修改成功'); setEdit(null); reload(); }}>
      <Space direction='vertical' style={{ width: '100%' }}>
        <Input placeholder='用户名' value={editUsername} onChange={(e) => setEditUsername(e.target.value)} />
        <Input placeholder='客户名' value={editCustomerName} onChange={(e) => setEditCustomerName(e.target.value)} />
        <Input.Password placeholder='新密码（留空不改）' value={pwd} onChange={(e) => setPwd(e.target.value)} />
        <div>激活状态：<Switch checked={active} onChange={setActive} /></div>
      </Space>
    </Modal>
  </Card>;
}

function ItemAdminPanel({ items, kw, setKw, load, authHeaders }) {
  const [edit, setEdit] = useState(null);
  const [newItem, setNewItem] = useState({ jan: '', brand: '', name: '', spec: '', msrp_price: undefined, in_qty: undefined, is_active: true });
  const cols = [{ title: 'JAN', dataIndex: 'jan' }, { title: '品牌', dataIndex: 'brand' }, { title: '商品名', dataIndex: 'name' }, { title: '零售价', dataIndex: 'msrp_price' }, { title: '入数', dataIndex: 'in_qty' }, { title: '操作', render: (_, r) => <Button className='click-btn' onClick={() => setEdit(r)}>修改</Button> }];
  return <Card className='panel' title='商品信息管理'>
    <Space wrap>
      <Input placeholder='按JAN或关键字检索' value={kw} onChange={(e) => setKw(e.target.value)} />
      <Button className='click-btn' onClick={load}>搜索</Button>
      <Button className='click-btn' onClick={async () => {
        const resp = await api.get('/api/items/import-template', { ...authHeaders, responseType: 'blob' });
        const url = window.URL.createObjectURL(new Blob([resp.data]));
        const a = document.createElement('a'); a.href = url; a.download = 'item_template.xlsx'; a.click();
        window.URL.revokeObjectURL(url);
      }}>下载导入模板</Button>
      <Upload accept='.xlsx' showUploadList={false} customRequest={async ({ file, onSuccess, onError }) => { try { const fd = new FormData(); fd.append('file', file); await api.post('/api/items/import-excel', fd, { ...authHeaders, headers: { ...authHeaders.headers, 'Content-Type': 'multipart/form-data' } }); message.success('批量导入成功'); load(); onSuccess('ok'); } catch (e) { message.error(e?.response?.data?.detail || '导入失败'); onError(e); } }}><Button className='click-btn' icon={<UploadOutlined />}>批量导入Excel</Button></Upload>
    </Space>
    <Space wrap style={{ marginTop: 8 }}>
      <Input placeholder='JAN' value={newItem.jan} onChange={(e) => setNewItem({ ...newItem, jan: e.target.value })} />
      <Input placeholder='品牌' value={newItem.brand} onChange={(e) => setNewItem({ ...newItem, brand: e.target.value })} />
      <Input placeholder='商品名' value={newItem.name} onChange={(e) => setNewItem({ ...newItem, name: e.target.value })} />
      <InputNumber min={0} placeholder='建议价' value={newItem.msrp_price} onChange={(v) => setNewItem({ ...newItem, msrp_price: v ?? undefined })} />
      <InputNumber min={1} placeholder='入数' value={newItem.in_qty} onChange={(v) => setNewItem({ ...newItem, in_qty: v ?? undefined })} />
      <Button className='click-btn' type='primary' onClick={async () => { await api.post('/api/items', newItem, authHeaders); message.success('手动新增商品成功'); setNewItem({ jan: '', brand: '', name: '', spec: '', msrp_price: undefined, in_qty: undefined, is_active: true }); load(); }}>手动新增商品</Button>
    </Space>
    <Table rowKey='id' dataSource={items} columns={cols} style={{ marginTop: 8 }} />
    <Modal open={!!edit} title='修改商品信息' onCancel={() => setEdit(null)} onOk={async () => { await api.patch(`/api/items/${edit.id}`, edit, authHeaders); message.success('修改成功'); setEdit(null); load(); }}>
      {edit && <Space direction='vertical' style={{ width: '100%' }}><Input value={edit.jan} onChange={(e) => setEdit({ ...edit, jan: e.target.value })} /><Input value={edit.brand} onChange={(e) => setEdit({ ...edit, brand: e.target.value })} /><Input value={edit.name} onChange={(e) => setEdit({ ...edit, name: e.target.value })} /><InputNumber value={edit.msrp_price} onChange={(v) => setEdit({ ...edit, msrp_price: v || 0 })} style={{ width: '100%' }} placeholder='零售价' /><InputNumber value={edit.in_qty} onChange={(v) => setEdit({ ...edit, in_qty: v || 1 })} style={{ width: '100%' }} /></Space>}
    </Modal>
  </Card>;
}

function MergeBillBox({ orderIds, authHeaders, reload }) {
  const [price, setPrice] = useState(1);
  return <Space style={{ marginTop: 8 }}><InputNumber min={1} value={price} onChange={(v) => setPrice(v || 1)} /><Button className='click-btn' type='primary' onClick={async () => { await api.post('/api/bills/from-orders', { order_ids: orderIds, sale_unit_price: price }, authHeaders); message.success('已合并生成新账单'); reload(); }}>合并选中订单生成账单</Button></Space>;
}

function AdminBills({ role, authHeaders, bills, customers, allocations, reload }) {
  const [c, setC] = useState(); const [ids, setIds] = useState(''); const [price, setPrice] = useState(1); const [bid, setBid] = useState(); const [act, setAct] = useState('pay');
  const [editBill, setEditBill] = useState(null);
  const cnStatus = (t, v) => ({
    status: { draft: '草稿', issued: '已开立', archived: '已归档' },
    payment_status: { unpaid: '未付款', paid: '已付款', received: '已收款' },
    shipping_status: { not_shipped: '未发货', shipped: '已发货', delivered: '已收货' },
  }[t][v] || v);
  const activeBills = bills.filter(b => b.status !== 'archived').map(b => ({ ...b, customer_name: customers.find(cu => cu.id === b.customer_id)?.name || `客户${b.customer_id}` }));
  return <Card className='panel' title='账单管理'>
    {role === 'super_admin' && <Space><Select placeholder='客户' style={{ width: 180 }} options={customers.map(x => ({ label: x.name, value: x.id }))} onChange={setC} /><Input placeholder='分配ID 例 1,2' style={{ width: 220 }} value={ids} onChange={(e) => setIds(e.target.value)} /><InputNumber min={1} value={price} onChange={(v) => setPrice(v || 1)} /><Button className='click-btn' onClick={async () => { await api.post('/api/bills', { customer_id: c, allocation_ids: ids.split(',').map(s => Number(s.trim())).filter(Boolean), sale_unit_price: price }, authHeaders); message.success('账单生成成功'); reload(); }}>生成账单</Button></Space>}
    <Space style={{ marginTop: 8 }}><Select placeholder='选择账单' style={{ width: 180 }} options={activeBills.map(b => ({ label: b.bill_no, value: b.id }))} onChange={setBid} /><Select style={{ width: 180 }} value={act} onChange={setAct} options={[{ label: '付款', value: 'pay' }, { label: '确认收款', value: 'confirm_receipt' }, { label: '发货', value: 'ship' }, { label: '收货', value: 'deliver' }, { label: '归档', value: 'archive' }]} /><Button className='click-btn' onClick={async () => { await api.post(`/api/bills/${bid}/state`, { action: act }, authHeaders); message.success('状态更新成功'); reload(); }}>状态推进</Button></Space>
    <Table rowKey='id' dataSource={activeBills} columns={[
      { title: '账单号', dataIndex: 'bill_no' },
      ...(role === 'super_admin' ? [{ title: '客户名', dataIndex: 'customer_name' }] : []),
      { title: '金额', dataIndex: 'total_amount' },
      { title: '账单状态', dataIndex: 'status', render: (v) => cnStatus('status', v) },
      { title: '付款状态', dataIndex: 'payment_status', render: (v) => cnStatus('payment_status', v) },
      { title: '物流状态', dataIndex: 'shipping_status', render: (v) => cnStatus('shipping_status', v) },
      { title: '操作', render: (_, r) => <Button className='click-btn' onClick={() => setEditBill({ ...r })}>修改账单</Button> },
    ]} style={{ marginTop: 8 }} />

    <Modal
      open={!!editBill}
      title='修改账单'
      onCancel={() => setEditBill(null)}
      onOk={async () => {
        await api.patch(`/api/bills/${editBill.id}`, {
          bill_no: editBill.bill_no,
          total_amount: editBill.total_amount,
          status: editBill.status,
          payment_status: editBill.payment_status,
          shipping_status: editBill.shipping_status,
        }, authHeaders);
        message.success('账单修改成功');
        setEditBill(null);
        reload();
      }}
    >
      {editBill && <Space direction='vertical' style={{ width: '100%' }}>
        <Input value={editBill.bill_no} onChange={(e) => setEditBill({ ...editBill, bill_no: e.target.value })} placeholder='账单号' />
        <InputNumber style={{ width: '100%' }} min={0} value={editBill.total_amount} onChange={(v) => setEditBill({ ...editBill, total_amount: v || 0 })} placeholder='金额' />
        <Select value={editBill.status} onChange={(v) => setEditBill({ ...editBill, status: v })} options={[{ label: '草稿', value: 'draft' }, { label: '已开立', value: 'issued' }, { label: '已归档', value: 'archived' }]} />
        <Select value={editBill.payment_status} onChange={(v) => setEditBill({ ...editBill, payment_status: v })} options={[{ label: '未付款', value: 'unpaid' }, { label: '已付款', value: 'paid' }, { label: '已收款', value: 'received' }]} />
        <Select value={editBill.shipping_status} onChange={(v) => setEditBill({ ...editBill, shipping_status: v })} options={[{ label: '未发货', value: 'not_shipped' }, { label: '已发货', value: 'shipped' }, { label: '已收货', value: 'delivered' }]} />
      </Space>}
    </Modal>
  </Card>;
}
