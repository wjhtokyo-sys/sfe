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
  const [data, setData] = useState({ items: [], orders: [], bills: [], customers: [], lots: [], allocations: [], superCustomers: [], adminUsers: [] });
  const [orderPick, setOrderPick] = useState([]);
  const [fifoLot, setFifoLot] = useState({ item_id: undefined, qty_received: 1 });
  const [fifoOrderId, setFifoOrderId] = useState();
  const [orderCustomerFilter, setOrderCustomerFilter] = useState();
  const [refreshing, setRefreshing] = useState(false);

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
    setRefreshing(true);
    try {
      const ts = Date.now();
      const noCacheHeaders = { ...authHeaders, headers: { ...authHeaders.headers, 'Cache-Control': 'no-cache', Pragma: 'no-cache' } };
      const meInfo = await api.get(`/auth/me?_ts=${ts}`, noCacheHeaders).then(r => r.data);
      setMe(meInfo);
      const req = (u) => {
        const sep = u.includes('?') ? '&' : '?';
        return api.get(`${u}${sep}_ts=${ts}`, noCacheHeaders).then(r => r.data).catch(() => []);
      };
      const [items, orders, bills, customers, lots, allocations, superCustomers, adminUsers] = await Promise.all([
        req(`/api/items${kw ? `?keyword=${encodeURIComponent(kw)}` : ''}`),
        req('/api/orders'), req('/api/bills'), req('/api/customers'), req('/api/lots'), req('/api/allocations'), req('/api/super/customers'), req('/api/super/admin-users'),
      ]);
      setData({ items, orders, bills, customers, lots, allocations, superCustomers, adminUsers });
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => { if (token) load(); }, [token]);

  useEffect(() => {
    if (!token) return;
    if (role === 'super_admin') setMenu('items_admin');
    if (role === 'customer') setMenu('items');
  }, [token, role]);

  // 全局双击预防：所有 click-btn 按钮点击后短暂锁定，防止重复提交
  useEffect(() => {
    const onClickCapture = (evt) => {
      const btn = evt.target?.closest?.('button.click-btn');
      if (!btn) return;
      if (btn.disabled || btn.dataset.locked === '1') {
        evt.preventDefault();
        evt.stopPropagation();
        return;
      }
      btn.dataset.locked = '1';
      const oldPointer = btn.style.pointerEvents;
      btn.style.pointerEvents = 'none';
      setTimeout(() => {
        btn.dataset.locked = '0';
        btn.style.pointerEvents = oldPointer || '';
      }, 800);
    };
    document.addEventListener('click', onClickCapture, true);
    return () => document.removeEventListener('click', onClickCapture, true);
  }, []);

  if (!token) return <div className='page'>
    <Title level={3}>SFE 登录入口</Title>
    <Card title='客户登录入口页' className='login-wrap'><Form onFinish={(v) => login('/auth/customer-login', v)}><Form.Item name='username' rules={[{ required: true }]}><Input placeholder='客户账号' /></Form.Item><Form.Item name='password' rules={[{ required: true }]}><Input.Password placeholder='密码' /></Form.Item><Button className='click-btn' htmlType='submit' type='primary'>客户登录</Button></Form></Card>
    <Card title='管理员登录入口页' className='login-wrap'><Form onFinish={(v) => login('/auth/admin-login', v)}><Form.Item name='username' rules={[{ required: true }]}><Input placeholder='管理员账号' /></Form.Item><Form.Item name='password' rules={[{ required: true }]}><Input.Password placeholder='密码' /></Form.Item><Button className='click-btn' htmlType='submit' type='primary'>管理员登录</Button></Form></Card>
  </div>;

  const customerMenus = [{ key: 'items', label: '商品信息查询' }, { key: 'orders', label: '订单管理' }, { key: 'bills', label: '账单管理' }, { key: 'history', label: '历史账单' }];
  const adminMenus = [{ key: 'items_admin', label: '商品信息管理' }, { key: 'orders', label: '客户订单管理' }, { key: 'purchase_orders', label: '进货单管理' }, { key: 'arrival_unchecked', label: '到货一览' }, { key: 'fifo', label: 'FIFO管理' }, { key: 'bills', label: '账单管理' }, { key: 'history', label: '历史账单' }, { key: 'suppliers', label: '供应商管理' }, { key: 'customers', label: '账号管理' }, { key: 'db_ops', label: '数据库操作' }];

  const customerItemCols = [
    { title: 'JAN', dataIndex: 'jan' }, { title: '品牌', dataIndex: 'brand' }, { title: '商品名', dataIndex: 'name' }, { title: '零售价', dataIndex: 'msrp_price' }, { title: '入数', dataIndex: 'in_qty' },
    { title: '操作', render: (_, row) => <CustomerOrderBtn row={row} me={me} authHeaders={authHeaders} reload={load} /> },
  ];

  const orderCols = [{ title: '订单ID', dataIndex: 'id' }, { title: role === 'super_admin' ? '客户名' : '客户ID', dataIndex: 'customer_id', render: (v) => role === 'super_admin' ? (data.customers.find(c => c.id === v)?.name || `客户${v}`) : v }, { title: 'JAN', dataIndex: 'jan_snapshot' }, { title: '商品', dataIndex: 'item_name_snapshot' }, { title: '订货', dataIndex: 'qty_requested' }, { title: '已到货', dataIndex: 'qty_allocated' }, ...(role === 'super_admin' ? [{ title: '订货时间', dataIndex: 'created_at', render: (v) => { const d = v ? new Date(v) : null; if (!d || Number.isNaN(d.getTime())) return '-'; const y = d.getFullYear(); const m = String(d.getMonth() + 1).padStart(2, '0'); const day = String(d.getDate()).padStart(2, '0'); return `${y}年${m}月${day}日`; } }] : []), { title: '操作', render: (_, r) => <Popconfirm title='确认删除该订单？' onConfirm={async () => { await api.delete(`/api/orders/${r.id}`, authHeaders); message.success('订单已删除'); load(); }}><Button className='click-btn' danger>删除</Button></Popconfirm> }];

  const billCols = [{ title: '账单号', dataIndex: 'bill_no' }, { title: '金额', dataIndex: 'total_amount' }, { title: '账单状态', dataIndex: 'status' }, { title: '付款状态', dataIndex: 'payment_status' }, { title: '物流状态', dataIndex: 'shipping_status' }];

  return <Layout style={{ minHeight: '100vh' }}>
    <Sider>
      <div style={{ color: '#fff', padding: 16 }}>
        <div>{role === 'customer' ? '客户管理页' : '超级管理员管理页'}</div>
        {role === 'customer' && <div style={{ marginTop: 6, color: '#ffd666', fontSize: 12 }}>当前登录中：{me?.customer_name || me?.username || '-'}</div>}
      </div>
      <Menu theme='dark' mode='inline' selectedKeys={[menu]} items={role === 'customer' ? customerMenus : adminMenus} onClick={(e) => setMenu(e.key)} />
    </Sider>
    <Layout><Content className='page'>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <Space><Button className='click-btn' loading={refreshing} onClick={load}>{refreshing ? '刷新中...' : '刷新'}</Button></Space>
        <Button className='click-btn' danger onClick={logout}>登出</Button>
      </div>

      {role === 'customer' && menu === 'items' && <Card className='panel' title='商品信息查询'>
        <Space><Input placeholder='按JAN或关键字检索' value={kw} onChange={(e) => setKw(e.target.value)} /><Button className='click-btn' onClick={load}>搜索</Button></Space>
        <Table rowKey='id' dataSource={data.items} columns={customerItemCols} style={{ marginTop: 8 }} />
      </Card>}

      {menu === 'orders' && <Card className='panel' title={role === 'super_admin' ? '客户订单管理' : '订单管理'}>
        {role === 'super_admin' && <Space style={{ marginBottom: 8 }}>
          <Select
            allowClear
            placeholder='客户名'
            style={{ width: 220 }}
            value={orderCustomerFilter}
            options={data.customers.map(c => ({ label: c.name, value: c.id }))}
            onChange={setOrderCustomerFilter}
          />
        </Space>}
        <Table rowKey='id' dataSource={(role === 'super_admin' ? data.orders.filter(o => o.status === 'open') : data.orders).filter(o => !orderCustomerFilter || o.customer_id === orderCustomerFilter)} columns={orderCols} />
      </Card>}

      {menu === 'bills' && <AdminBills role={role} authHeaders={authHeaders} bills={data.bills} customers={data.customers} allocations={data.allocations} reload={load} />}
      {menu === 'history' && <HistoryBillsPanel role={role} bills={data.bills} customers={data.customers} authHeaders={authHeaders} />}

      {role !== 'customer' && menu === 'suppliers' && <SupplierPanel authHeaders={authHeaders} />}

      {role !== 'customer' && menu === 'customers' && <AccountManagePage customerRows={data.superCustomers} customers={data.customers} adminUsers={data.adminUsers} authHeaders={authHeaders} reload={load} />}
      {role !== 'customer' && menu === 'db_ops' && <DatabaseOpsPanel authHeaders={authHeaders} />}

      {role !== 'customer' && menu === 'items_admin' && <ItemAdminPanel items={data.items} kw={kw} setKw={setKw} load={load} authHeaders={authHeaders} />}

      {role !== 'customer' && menu === 'purchase_orders' && <PurchaseOrderPanel authHeaders={authHeaders} />}

      {role !== 'customer' && menu === 'arrival_unchecked' && <ArrivalOverviewPanel authHeaders={authHeaders} />}

      {role !== 'customer' && menu === 'fifo' && <FifoPendingPanel authHeaders={authHeaders} customers={data.customers} orders={data.orders} />}

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

function SuperCustomerPanel({ rows, customers, authHeaders, reload }) {
  const [edit, setEdit] = useState(null); const [pwd, setPwd] = useState(''); const [active, setActive] = useState(true);
  const [editUsername, setEditUsername] = useState('');
  const [editCustomerName, setEditCustomerName] = useState('');
  const [newUser, setNewUser] = useState({ username: '', password: '', customer_name: '' });
  const mergedRows = [...rows, ...customers.filter(c => !rows.find(r => r.customer_id === c.id)).map(c => ({ user_id: null, username: '-', is_active: c.is_active, customer_id: c.id, customer_name: c.name, customer_active: c.is_active }))];
  const cols = [
    { title: '用户名', dataIndex: 'username' }, { title: '客户名', dataIndex: 'customer_name' }, { title: '激活', dataIndex: 'is_active', render: (v) => <Tag>{v ? '启用' : '停用'}</Tag> },
    { title: '操作', render: (_, r) => <Space><Button className='click-btn' onClick={() => { setEdit(r); setPwd(''); setActive(r.is_active); setEditUsername(r.username || ''); setEditCustomerName(r.customer_name || ''); }}>修改</Button><Popconfirm title='确认删除客户？' onConfirm={async () => { try { if (r.user_id) await api.delete(`/api/super/customers/${r.user_id}`, authHeaders); else await api.delete(`/api/super/customers/customer/${r.customer_id}`, authHeaders); message.success('已删除'); reload(); } catch (e) { message.error(e?.response?.data?.detail || '删除失败'); } }}><Button className='click-btn' danger>删除</Button></Popconfirm></Space> },
  ];
  return <Card className='panel' title='客户账号管理'>
    <Space wrap style={{ marginBottom: 8 }}>
      <Input placeholder='客户登录账号' value={newUser.username} onChange={(e) => setNewUser({ ...newUser, username: e.target.value })} />
      <Input.Password placeholder='客户登录密码' value={newUser.password} onChange={(e) => setNewUser({ ...newUser, password: e.target.value })} />
      <Input placeholder='客户名称' value={newUser.customer_name} onChange={(e) => setNewUser({ ...newUser, customer_name: e.target.value })} />
      <Button className='click-btn' type='primary' onClick={async () => { await api.post('/api/super/customers', newUser, authHeaders); message.success('新增客户成功'); setNewUser({ username: '', password: '', customer_name: '' }); reload(); }}>新增客户</Button>
    </Space>
    <Table rowKey={(r) => r.user_id || `c-${r.customer_id}`} columns={cols} dataSource={mergedRows} />
    <Modal open={!!edit} title='修改客户账号' onCancel={() => setEdit(null)} onOk={async () => { if (edit.user_id) { await api.patch(`/api/super/customers/${edit.user_id}`, { username: editUsername || undefined, customer_name: editCustomerName || undefined, password: pwd || undefined, is_active: active }, authHeaders); } else { await api.patch(`/api/super/customers/customer/${edit.customer_id}`, { customer_name: editCustomerName || undefined, is_active: active }, authHeaders); } message.success('修改成功'); setEdit(null); reload(); }}>
      <Space direction='vertical' style={{ width: '100%' }}>
        <Input placeholder='用户名' value={editUsername} onChange={(e) => setEditUsername(e.target.value)} />
        <Input placeholder='客户名' value={editCustomerName} onChange={(e) => setEditCustomerName(e.target.value)} />
        <Input.Password placeholder='新密码（留空不改）' value={pwd} onChange={(e) => setPwd(e.target.value)} />
        <div>激活状态：<Switch checked={active} onChange={setActive} /></div>
      </Space>
    </Modal>
  </Card>;
}

function AdminAccountPanel({ adminUsers, authHeaders, reload }) {
  const [edit, setEdit] = useState(null);
  const [newUser, setNewUser] = useState({ username: '', password: '', role: 'admin' });
  const cols = [
    { title: '用户名', dataIndex: 'username' },
    { title: '角色', dataIndex: 'role' },
    { title: '激活', dataIndex: 'is_active', render: (v) => <Tag>{v ? '启用' : '停用'}</Tag> },
    { title: '操作', render: (_, r) => <Space><Button className='click-btn' onClick={() => setEdit({ ...r, password: '' })}>修改</Button><Popconfirm title='确认删除管理账号？' onConfirm={async () => { try { await api.delete(`/api/super/admin-users/${r.user_id}`, authHeaders); message.success('已删除'); reload(); } catch (e) { message.error(e?.response?.data?.detail || '删除失败'); } }}><Button className='click-btn' danger>删除</Button></Popconfirm></Space> },
  ];
  return <Card className='panel' title='管理账号管理'>
    <Space wrap style={{ marginBottom: 8 }}>
      <Input placeholder='管理账号' value={newUser.username} onChange={(e) => setNewUser({ ...newUser, username: e.target.value })} />
      <Input.Password placeholder='密码' value={newUser.password} onChange={(e) => setNewUser({ ...newUser, password: e.target.value })} />
      <Select style={{ width: 160 }} value={newUser.role} onChange={(v) => setNewUser({ ...newUser, role: v })} options={[{ label: '管理员', value: 'admin' }, { label: '超级管理员', value: 'super_admin' }]} />
      <Button className='click-btn' type='primary' onClick={async () => { try { await api.post('/api/super/admin-users', newUser, authHeaders); message.success('新增管理账号成功'); setNewUser({ username: '', password: '', role: 'admin' }); reload(); } catch (e) { message.error(e?.response?.data?.detail || '新增失败'); } }}>新增管理账号</Button>
    </Space>
    <Table rowKey='user_id' columns={cols} dataSource={adminUsers || []} />
    <Modal open={!!edit} title='修改管理账号' onCancel={() => setEdit(null)} onOk={async () => { try { await api.patch(`/api/super/admin-users/${edit.user_id}`, { username: edit.username, password: edit.password || undefined, role: edit.role, is_active: edit.is_active }, authHeaders); message.success('修改成功'); setEdit(null); reload(); } catch (e) { message.error(e?.response?.data?.detail || '修改失败'); } }}>
      {edit && <Space direction='vertical' style={{ width: '100%' }}>
        <Input value={edit.username} onChange={(e) => setEdit({ ...edit, username: e.target.value })} />
        <Input.Password placeholder='新密码（留空不改）' value={edit.password} onChange={(e) => setEdit({ ...edit, password: e.target.value })} />
        <Select value={edit.role} onChange={(v) => setEdit({ ...edit, role: v })} options={[{ label: '管理员', value: 'admin' }, { label: '超级管理员', value: 'super_admin' }]} />
        <div>激活状态：<Switch checked={!!edit.is_active} onChange={(v) => setEdit({ ...edit, is_active: v })} /></div>
      </Space>}
    </Modal>
  </Card>;
}

function AccountManagePage({ customerRows, customers, adminUsers, authHeaders, reload }) {
  return <>
    <SuperCustomerPanel rows={customerRows} customers={customers} authHeaders={authHeaders} reload={reload} />
    <AdminAccountPanel adminUsers={adminUsers} authHeaders={authHeaders} reload={reload} />
  </>;
}

function ItemAdminPanel({ items, kw, setKw, load, authHeaders }) {
  const [edit, setEdit] = useState(null);
  const [newItem, setNewItem] = useState({ jan: '', brand: '', name: '', spec: '', msrp_price: undefined, in_qty: undefined, is_active: true });
  const cols = [{ title: 'JAN', dataIndex: 'jan' }, { title: '品牌', dataIndex: 'brand' }, { title: '商品名', dataIndex: 'name' }, { title: '零售价', dataIndex: 'msrp_price' }, { title: '入数', dataIndex: 'in_qty' }, { title: '操作', render: (_, r) => <Space><Button className='click-btn' onClick={() => setEdit(r)}>修改</Button><Popconfirm title='确认删除该商品？' onConfirm={async () => { await api.delete(`/api/items/${r.id}`, authHeaders); message.success('删除成功'); load(); }}><Button className='click-btn' danger>删除</Button></Popconfirm></Space> }];
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
      <Upload accept='.xlsx' showUploadList={false} customRequest={async ({ file, onSuccess, onError }) => { try { Modal.confirm({ title: '确认导入', content: `确认导入文件：${file?.name || ''}？`, onOk: async () => { const fd = new FormData(); fd.append('file', file); await api.post('/api/items/import-excel', fd, { ...authHeaders, headers: { ...authHeaders.headers, 'Content-Type': 'multipart/form-data' } }); message.success('批量导入成功'); load(); onSuccess('ok'); }, onCancel: () => onError(new Error('cancelled')) }); } catch (e) { message.error(e?.response?.data?.detail || '导入失败'); onError(e); } }}><Button className='click-btn' icon={<UploadOutlined />}>批量导入Excel</Button></Upload>
    </Space>
    <Space wrap style={{ marginTop: 8 }}>
      <Input placeholder='JAN' value={newItem.jan} onChange={(e) => setNewItem({ ...newItem, jan: e.target.value })} />
      <Input placeholder='品牌' value={newItem.brand} onChange={(e) => setNewItem({ ...newItem, brand: e.target.value })} />
      <Input placeholder='商品名' value={newItem.name} onChange={(e) => setNewItem({ ...newItem, name: e.target.value })} />
      <InputNumber min={0} placeholder='建议价' value={newItem.msrp_price} onChange={(v) => setNewItem({ ...newItem, msrp_price: v ?? undefined })} />
      <InputNumber min={1} placeholder='入数' value={newItem.in_qty} onChange={(v) => setNewItem({ ...newItem, in_qty: v ?? undefined })} />
      <Button className='click-btn' type='primary' onClick={async () => {
        const missing = [];
        if (!String(newItem.jan || '').trim()) missing.push('JAN');
        if (!String(newItem.brand || '').trim()) missing.push('品牌');
        if (!String(newItem.name || '').trim()) missing.push('商品名');
        if (newItem.msrp_price === undefined || newItem.msrp_price === null || newItem.msrp_price === '') missing.push('建议价');
        if (newItem.in_qty === undefined || newItem.in_qty === null || newItem.in_qty === '') missing.push('入数');
        if (missing.length) { message.error(`以下为必填项，不能提交：${missing.join('、')}`); return; }
        try {
          await api.post('/api/items', newItem, authHeaders);
          message.success('手动新增商品成功');
          setNewItem({ jan: '', brand: '', name: '', spec: '', msrp_price: undefined, in_qty: undefined, is_active: true });
          load();
        } catch (e) {
          message.error(e?.response?.data?.detail || '提交失败');
        }
      }}>手动新增商品</Button>
    </Space>
    <Table rowKey='id' dataSource={items} columns={cols} style={{ marginTop: 8 }} />
    <Modal open={!!edit} title='修改商品信息' onCancel={() => setEdit(null)} onOk={async () => { await api.patch(`/api/items/${edit.id}`, edit, authHeaders); message.success('修改成功'); setEdit(null); load(); }}>
      {edit && <Space direction='vertical' style={{ width: '100%' }}><Input value={edit.jan} onChange={(e) => setEdit({ ...edit, jan: e.target.value })} /><Input value={edit.brand} onChange={(e) => setEdit({ ...edit, brand: e.target.value })} /><Input value={edit.name} onChange={(e) => setEdit({ ...edit, name: e.target.value })} /><InputNumber value={edit.msrp_price} onChange={(v) => setEdit({ ...edit, msrp_price: v || 0 })} style={{ width: '100%' }} placeholder='零售价' /><InputNumber value={edit.in_qty} onChange={(v) => setEdit({ ...edit, in_qty: v || 1 })} style={{ width: '100%' }} /></Space>}
    </Modal>
  </Card>;
}

function SupplierPanel({ authHeaders }) {
  const [rows, setRows] = useState([]);
  const [edit, setEdit] = useState(null);
  const [form, setForm] = useState({ supplier_code: '', name: '' });
  const load = async () => setRows(await api.get('/api/suppliers', authHeaders).then(r => r.data));
  useEffect(() => { load(); }, []);
  return <Card className='panel' title='供应商管理'>
    <Space style={{ marginBottom: 8 }}>
      <Input placeholder='供应商编码' value={form.supplier_code} onChange={(e) => setForm({ ...form, supplier_code: e.target.value })} />
      <Input placeholder='供应商名' value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
      <Button className='click-btn' type='primary' onClick={async () => { await api.post('/api/suppliers', form, authHeaders); setForm({ supplier_code: '', name: '' }); load(); }}>追加</Button>
    </Space>
    <Table rowKey='id' dataSource={rows} columns={[
      { title: '供应商ID', dataIndex: 'id' },
      { title: '供应商编码', dataIndex: 'supplier_code' },
      { title: '供应商名', dataIndex: 'name' },
      { title: '操作', render: (_, r) => <Space><Button className='click-btn' onClick={() => setEdit({ ...r })}>修改</Button><Popconfirm title='确认删除供应商？' onConfirm={async () => { await api.delete(`/api/suppliers/${r.id}`, authHeaders); load(); }}><Button className='click-btn' danger>删除</Button></Popconfirm></Space> },
    ]} />
    <Modal open={!!edit} title='修改供应商' onCancel={() => setEdit(null)} onOk={async () => { await api.patch(`/api/suppliers/${edit.id}`, { supplier_code: edit.supplier_code, name: edit.name }, authHeaders); setEdit(null); load(); }}>
      {edit && <Space direction='vertical' style={{ width: '100%' }}><Input value={edit.supplier_code} onChange={(e) => setEdit({ ...edit, supplier_code: e.target.value })} /><Input value={edit.name} onChange={(e) => setEdit({ ...edit, name: e.target.value })} /></Space>}
    </Modal>
  </Card>;
}

function PurchaseOrderPanel({ authHeaders }) {
  const [rows, setRows] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [items, setItems] = useState([]);
  const [importSupplierId, setImportSupplierId] = useState();
  const [manualSupplierId, setManualSupplierId] = useState();
  const [pickedPoIds, setPickedPoIds] = useState([]);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailRows, setDetailRows] = useState([]);
  const [lineRows, setLineRows] = useState([{ jan: '', item_name: '', qty: undefined, unit_cost: undefined }]);

  const load = async () => {
    const [po, sp, it] = await Promise.all([
      api.get('/api/purchase-orders', authHeaders).then(r => r.data),
      api.get('/api/suppliers', authHeaders).then(r => r.data),
      api.get('/api/items', authHeaders).then(r => r.data),
    ]);
    setRows(po); setSuppliers(sp); setItems(it || []);
  };
  useEffect(() => { load(); }, []);

  const statusTag = (v) => v === 'checked_inbound' ? <Tag color='green'>已盘点入库</Tag> : <Tag color='red'>已创建未盘点</Tag>;
  const payTag = (v) => v === 'paid' ? <Tag color='green'>已支付</Tag> : <Tag color='red'>未支付</Tag>;
  const fmtDate = (v) => { const d = v ? new Date(v) : null; if (!d || Number.isNaN(d.getTime())) return '-'; const y = d.getFullYear(); const m = String(d.getMonth() + 1).padStart(2, '0'); const day = String(d.getDate()).padStart(2, '0'); return `${y}年${m}月${day}日`; };
  const handleJanPaste = (e, startIdx) => {
    const text = e.clipboardData?.getData('text') || '';
    if (!text.includes('\n') && !text.includes('\t')) return;
    const lines = text.split(/\r?\n/).map(x => x.trim()).filter(Boolean);
    if (!lines.length) return;
    const parsed = lines.map(line => line.split('\t')).filter(cols => cols.length >= 4);
    if (!parsed.length) return;
    e.preventDefault();
    const next = [...lineRows];
    while (next.length < startIdx + parsed.length) next.push({ jan: '', item_name: '', qty: undefined, unit_cost: undefined });
    parsed.forEach((cols, i) => {
      next[startIdx + i] = {
        jan: (cols[0] || '').trim(),
        item_name: (cols[1] || '').trim(),
        qty: cols[2] !== '' ? Number(cols[2]) : undefined,
        unit_cost: cols[3] !== '' ? Number(cols[3]) : undefined,
      };
    });
    setLineRows(next);
  };

  return <Card className='panel' title='进货单管理'>
    <Space wrap>
      <Button className='click-btn' onClick={async () => { const resp = await api.get('/api/purchase-orders/import-template', { ...authHeaders, responseType: 'blob' }); const url = window.URL.createObjectURL(new Blob([resp.data])); const a = document.createElement('a'); a.href = url; a.download = 'purchase_order_template.xlsx'; a.click(); window.URL.revokeObjectURL(url); }}>下载导入模板</Button>
      <Select placeholder='选择供应商（必选）' style={{ width: 220 }} value={importSupplierId} options={suppliers.map(s => ({ label: s.name, value: s.id }))} onChange={setImportSupplierId} />
      <Upload accept='.xlsx' showUploadList={false} customRequest={async ({ file, onSuccess, onError }) => { try { if (!importSupplierId) { message.error('请先选择供应商'); onError(new Error('missing supplier')); return; } Modal.confirm({ title: '确认导入', content: `确认导入文件：${file?.name || ''}？`, onOk: async () => { const fd = new FormData(); fd.append('supplier_id', importSupplierId); fd.append('file', file); const res = await api.post('/api/purchase-orders/import-excel', fd, { ...authHeaders, headers: { ...authHeaders.headers, 'Content-Type': 'multipart/form-data' } }); const supplierName = suppliers.find(s => s.id === importSupplierId)?.name || ''; message.success(`导入成功：进货单号 ${res.data?.po_no || ''}，导入行数 ${res.data?.rows || 0}，供应商名 ${supplierName}`); load(); onSuccess('ok'); }, onCancel: () => onError(new Error('cancelled')) }); } catch (e) { message.error(e?.response?.data?.detail || '导入失败'); onError(e); } }}><Button className='click-btn' icon={<UploadOutlined />} disabled={!importSupplierId}>批量导入</Button></Upload>
    </Space>

    <div style={{ marginTop: 8 }}>
      <Select placeholder='供应商名（手动添加）' style={{ width: 220 }} value={manualSupplierId} options={suppliers.map(s => ({ label: s.name, value: s.id }))} onChange={setManualSupplierId} />
    </div>

    {lineRows.map((row, idx) => <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'nowrap', justifyContent: 'flex-start' }} key={idx}>
      <Input style={{ width: '20ch' }} placeholder='JAN' value={row.jan} onPaste={(e) => handleJanPaste(e, idx)} onChange={(e) => setLineRows(lineRows.map((r, i) => i === idx ? { ...r, jan: e.target.value } : r))} />
      <Input style={{ width: '60ch' }} placeholder='品名' value={row.item_name} onFocus={() => {
        if ((row.item_name || '').trim()) return;
        const jan = (row.jan || '').trim();
        if (!jan) return;
        const hit = items.find(it => String(it.jan || '').trim() === jan);
        if (!hit) return;
        setLineRows(lineRows.map((r, i) => i === idx ? { ...r, item_name: hit.name || r.item_name } : r));
      }} onChange={(e) => setLineRows(lineRows.map((r, i) => i === idx ? { ...r, item_name: e.target.value } : r))} />
      <InputNumber style={{ width: '10ch' }} placeholder='数量' min={1} value={row.qty} onChange={(v) => setLineRows(lineRows.map((r, i) => i === idx ? { ...r, qty: v ?? undefined } : r))} />
      <InputNumber style={{ width: '15ch' }} placeholder='进货单价' min={0} value={row.unit_cost} onChange={(v) => setLineRows(lineRows.map((r, i) => i === idx ? { ...r, unit_cost: v ?? undefined } : r))} />
      {idx === 0 && <>
        <Button className='click-btn' onClick={() => setLineRows([...lineRows, { jan: '', item_name: '', qty: undefined, unit_cost: undefined }])}>行+</Button>
        <Button className='click-btn' onClick={() => lineRows.length > 1 && setLineRows(lineRows.slice(0, -1))}>行-</Button>
        <Button className='click-btn' type='primary' onClick={async () => {
          try {
            if (!manualSupplierId) { message.error('供应商名必填，不能添加'); return; }
            const hasEmpty = lineRows.some(r => !String(r.jan || '').trim() || !String(r.item_name || '').trim() || r.qty === undefined || r.qty === null || r.qty === '' || r.unit_cost === undefined || r.unit_cost === null || r.unit_cost === '');
            if (hasEmpty) { message.error('供应商名、JAN、品名、数量、单价均为必填，不能添加'); return; }
            const res = await api.post('/api/purchase-orders/lines', { supplier_id: manualSupplierId, lines: lineRows }, authHeaders);
            message.success(`手动添加成功：${res.data?.po_no || ''}（${res.data?.rows || 0}行）`);
            setLineRows([{ jan: '', item_name: '', qty: undefined, unit_cost: undefined }]);
            load();
          } catch (e) {
            message.error(e?.response?.data?.detail || '当前数据不完整，不能添加');
          }
        }}>手动添加进货单</Button>
      </>}
    </div>)}

    <div style={{ marginTop: 8, display: 'flex', justifyContent: 'flex-end' }}>
      <Popconfirm title='是否要回复进货单到初始状态' onConfirm={async () => { await api.post('/api/purchase-orders/reset-status', { ids: pickedPoIds }, authHeaders); message.success('已恢复初始状态'); setPickedPoIds([]); load(); }}>
        <Button className='click-btn' disabled={!pickedPoIds.length}>恢复按钮</Button>
      </Popconfirm>
    </div>

    <Table style={{ marginTop: 8 }} rowKey='id' rowSelection={{ selectedRowKeys: pickedPoIds, onChange: (keys) => setPickedPoIds(keys) }} dataSource={rows} columns={[
      { title: '进货单号', dataIndex: 'po_no' },
      { title: '进货时间', dataIndex: 'purchased_at', render: fmtDate },
      { title: '供应商名', dataIndex: 'supplier_id', render: (v) => suppliers.find(s => s.id === v)?.name || `供应商${v}` },
      { title: '合计进货价格', dataIndex: 'total_cost' },
      { title: '付款状态', dataIndex: 'payment_status', render: payTag },
      { title: '盘点状态', dataIndex: 'status', render: statusTag },
      {
        title: '操作', render: (_, r) => <Space>
          <Button className='click-btn' onClick={async () => { const res = await api.get(`/api/purchase-orders/${r.id}/lines`, authHeaders); setDetailRows(res.data || []); setDetailOpen(true); }}>到货详细</Button>
          {r.payment_status !== 'paid' && <Popconfirm title='确认已支付？' onConfirm={async () => { await api.post(`/api/purchase-orders/${r.id}/pay`, {}, authHeaders); message.success('已更新为已支付'); load(); }}><Button className='click-btn' type='primary'>支付完成</Button></Popconfirm>}
          {r.status === 'created_unchecked' && <Popconfirm title='确认盘点完成？' onConfirm={async () => { await api.post(`/api/purchase-orders/${r.id}/status`, { status: 'checked_inbound' }, authHeaders); message.success('盘点完成'); load(); }}><Button className='click-btn' type='primary'>盘点完成</Button></Popconfirm>}
          {r.payment_status !== 'paid' && <Popconfirm title='确认删除进货单？' onConfirm={async () => { await api.delete(`/api/purchase-orders/${r.id}`, authHeaders); message.success('删除成功'); load(); }}><Button className='click-btn' danger>删除</Button></Popconfirm>}
        </Space>
      },
    ]} />
    <Modal open={detailOpen} title='商品详细' footer={null} onCancel={() => setDetailOpen(false)} width={720}>
      <Table rowKey='id' pagination={false} dataSource={detailRows} columns={[
        { title: 'JAN', dataIndex: 'jan' },
        { title: '品名', dataIndex: 'item_name_snapshot' },
        { title: '数量', dataIndex: 'qty' },
        { title: '进货价', dataIndex: 'unit_cost' },
      ]} />
    </Modal>
  </Card>;
}

function FifoPendingPanel({ authHeaders, customers = [], orders = [] }) {
  const [rows, setRows] = useState([]); const [action, setAction] = useState('inbound_to_order');
  const [customerFilter, setCustomerFilter] = useState();
  const load = async () => setRows(await api.get('/api/fifo/pending', authHeaders).then(r => r.data));
  useEffect(() => { load(); }, []);
  const fmtDate = (v) => { const d = v ? new Date(v) : null; if (!d || Number.isNaN(d.getTime())) return '-'; const y = d.getFullYear(); const m = String(d.getMonth() + 1).padStart(2, '0'); const day = String(d.getDate()).padStart(2, '0'); return `${y}年${m}月${day}日`; };
  const commonCols = [
    { title: '进货单号', dataIndex: 'source_po_no' },
    { title: '进货日期', dataIndex: 'purchased_at', render: fmtDate },
    { title: 'JAN', dataIndex: 'jan' },
    { title: '品名', dataIndex: 'item_name' },
    { title: '数量', dataIndex: 'qty' },
    { title: '进货价格', dataIndex: 'unit_cost' },
    { title: '操作', render: (_, r) => <Space><Select style={{ width: 180 }} value={action} onChange={setAction} options={[{ label: '匹配订单后入库', value: 'inbound_to_order' }, { label: '转普通库存入库', value: 'inbound_stock' }, { label: '仅关闭任务', value: 'close_only' }]} /><Button className='click-btn' onClick={async () => { await api.post(`/api/fifo/pending/${r.id}/resolve`, { action }, authHeaders); message.success('已处理'); load(); }}>执行</Button><Popconfirm title='确认删除该挂起记录？' onConfirm={async () => { await api.delete(`/api/fifo/pending/${r.id}`, authHeaders); message.success('删除成功'); load(); }}><Button className='click-btn' danger>删除</Button></Popconfirm></Space> },
  ];
  const multiRowsRaw = rows.filter(r => r.reason_code === 'multi_customer_match' && r.status === 'pending');
  const multiRows = !customerFilter ? multiRowsRaw : multiRowsRaw.filter(r => orders.some(o => o.customer_id === customerFilter && o.jan_snapshot === r.jan));
  const noMatchRows = rows.filter(r => r.reason_code === 'no_order_match' && r.status === 'pending');
  return <Card className='panel' title='FIFO管理'>
    <Card size='small' title='多客户命中分配管理'>
      <Space style={{ marginBottom: 8 }}>
        <Select allowClear placeholder='客户名' style={{ width: 220 }} value={customerFilter} options={customers.map(c => ({ label: c.name, value: c.id }))} onChange={setCustomerFilter} />
      </Space>
      <Table rowKey='id' dataSource={multiRows} columns={commonCols} />
    </Card>
    <Card size='small' title='无匹配货品管理' style={{ marginTop: 8 }}>
      <Table rowKey='id' dataSource={noMatchRows} columns={commonCols} />
    </Card>
  </Card>;
}

function ArrivalOverviewPanel({ authHeaders }) {
  const [rows, setRows] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [customerId, setCustomerId] = useState();
  const [billRows, setBillRows] = useState([]);
  const [pickedIds, setPickedIds] = useState([]);
  const [saleMap, setSaleMap] = useState({});

  const load = async () => {
    const [arr, cs] = await Promise.all([
      api.get('/api/arrival-overview', authHeaders).then(r => r.data),
      api.get('/api/customers', authHeaders).then(r => r.data),
    ]);
    setRows(arr || []);
    setCustomers(cs || []);
  };
  const loadBillRows = async (cid) => {
    if (!cid) { setBillRows([]); setPickedIds([]); setSaleMap({}); return; }
    const data = await api.get(`/api/arrival-bill-candidates?customer_id=${cid}`, authHeaders).then(r => r.data);
    setBillRows(data || []);
    setPickedIds([]);
    setSaleMap({});
  };

  useEffect(() => { load(); }, []);
  const fmtDate = (v) => { const d = v ? new Date(v) : null; if (!d || Number.isNaN(d.getTime())) return '-'; const y = d.getFullYear(); const m = String(d.getMonth() + 1).padStart(2, '0'); const day = String(d.getDate()).padStart(2, '0'); return `${y}年${m}月${day}日`; };

  const selectedRows = billRows.filter(r => pickedIds.includes(r.allocation_id));
  const purchaseTotal = selectedRows.reduce((s, r) => s + (Number(r.purchase_unit_price || 0) * Number(r.qty || 0)), 0);
  const salesTotal = selectedRows.reduce((s, r) => s + (Number(saleMap[r.allocation_id] || 0) * Number(r.qty || 0)), 0);

  return <Card className='panel' title='到货一览'>
    <Card size='small' title='账单生成表'>
      <Space wrap style={{ marginBottom: 8 }}>
        <Select placeholder='客户名' style={{ width: 220 }} value={customerId} options={customers.map(c => ({ label: c.name, value: c.id }))} onChange={(v) => { setCustomerId(v); loadBillRows(v); }} />
        <span>账单进货价合计：{purchaseTotal.toFixed(2)}</span>
        <span>账单销售价合计：{salesTotal.toFixed(2)}</span>
        <Button className='click-btn' type='primary' disabled={!customerId || !pickedIds.length} onClick={async () => {
          const lines = pickedIds.map(id => ({ allocation_id: id, sale_unit_price: Number(saleMap[id] || 0) }));
          if (lines.some(x => !x.sale_unit_price || x.sale_unit_price <= 0)) { message.error('请填写所选行的销售价格'); return; }
          try {
            const res = await api.post('/api/bills/from-arrival', { customer_id: customerId, lines }, authHeaders);
            message.success(`生成账单成功：${res.data?.bill_no || ''}`);
            loadBillRows(customerId);
          } catch (e) {
            message.error(e?.response?.data?.detail || '生成账单失败');
          }
        }}>生成账单</Button>
      </Space>
      <Table rowKey='allocation_id' rowSelection={{ selectedRowKeys: pickedIds, onChange: (keys) => setPickedIds(keys) }} dataSource={billRows} columns={[
        { title: '进货日期', dataIndex: 'purchased_at', render: fmtDate },
        { title: 'JAN', dataIndex: 'jan' },
        { title: '品名', dataIndex: 'item_name' },
        { title: '数量', dataIndex: 'qty' },
        { title: '订货日期', dataIndex: 'order_date', render: fmtDate },
        { title: '采购价格', dataIndex: 'purchase_unit_price' },
        { title: '操作', render: (_, r) => <InputNumber min={0} placeholder='销售价格' value={saleMap[r.allocation_id]} onChange={(v) => setSaleMap({ ...saleMap, [r.allocation_id]: v || 0 })} /> },
      ]} />
    </Card>

    <Table style={{ marginTop: 8 }} rowKey={(r) => r.line_id ?? `${r.po_no}-${r.jan}`} dataSource={rows} columns={[
      { title: '进货单号', dataIndex: 'po_no' },
      { title: '进货日期', dataIndex: 'purchased_at', render: fmtDate },
      { title: 'JAN', dataIndex: 'jan' },
      { title: '品名', dataIndex: 'item_name' },
      { title: '客户名', dataIndex: 'customer_name' },
      { title: '数量', dataIndex: 'qty' },
      { title: '采购单价', dataIndex: 'unit_cost' },
      { title: '操作', render: (_, r) => <Popconfirm title='确认删除该到货明细？' onConfirm={async () => { try { await api.delete(`/api/purchase-order-lines/${r.line_id}`, authHeaders); message.success('删除成功'); load(); } catch (e) { message.error(e?.response?.data?.detail || '删除失败'); } }}><Button className='click-btn' danger>删除</Button></Popconfirm> },
    ]} />
  </Card>;
}

function DatabaseOpsPanel({ authHeaders }) {
  const [tables, setTables] = useState([]);
  const [tableName, setTableName] = useState();
  const [columns, setColumns] = useState([]);
  const [rows, setRows] = useState([]);
  const [jsonText, setJsonText] = useState('{}');
  const [editRow, setEditRow] = useState(null);

  const loadTables = async () => {
    const r = await api.get('/api/db/tables', authHeaders);
    setTables(r.data?.tables || []);
  };
  const loadRows = async (tb = tableName) => {
    if (!tb) return;
    const r = await api.get(`/api/db/table/${tb}?limit=200`, authHeaders);
    setColumns(r.data?.columns || []);
    setRows(r.data?.rows || []);
  };

  useEffect(() => { loadTables(); }, []);

  return <Card className='panel' title='数据库操作'>
    <Space wrap>
      <Select placeholder='选择表' style={{ width: 220 }} value={tableName} options={tables.map(t => ({ label: t, value: t }))} onChange={(v) => { setTableName(v); loadRows(v); }} />
      <Button className='click-btn' onClick={() => loadRows()}>读取表数据</Button>
    </Space>

    <Space style={{ marginTop: 8 }} align='start'>
      <Input.TextArea value={jsonText} onChange={(e) => setJsonText(e.target.value)} rows={4} style={{ width: 420 }} placeholder='新增数据 JSON，如 {"name":"x"}' />
      <Button className='click-btn' type='primary' onClick={async () => { try { const data = JSON.parse(jsonText || '{}'); await api.post(`/api/db/table/${tableName}`, { data }, authHeaders); message.success('添加成功'); loadRows(); } catch (e) { message.error(e?.response?.data?.detail || '添加失败'); } }}>添加</Button>
    </Space>

    <Table
      style={{ marginTop: 8 }}
      rowKey={(r) => r.id ?? JSON.stringify(r)}
      dataSource={rows}
      columns={[
        ...columns.slice(0, 8).map(c => ({ title: c, dataIndex: c })),
        { title: '操作', render: (_, r) => <Space>
          <Button className='click-btn' onClick={() => { setEditRow(r); setJsonText(JSON.stringify(r, null, 2)); }}>修改</Button>
          <Popconfirm title='确认删除该行？' onConfirm={async () => { try { await api.delete(`/api/db/table/${tableName}/${r.id}`, authHeaders); message.success('删除成功'); loadRows(); } catch (e) { message.error(e?.response?.data?.detail || '删除失败'); } }}>
            <Button className='click-btn' danger>删除</Button>
          </Popconfirm>
        </Space> },
      ]}
    />

    <Modal open={!!editRow} title='修改数据' onCancel={() => setEditRow(null)} onOk={async () => { try { const data = JSON.parse(jsonText || '{}'); await api.patch(`/api/db/table/${tableName}/${editRow.id}`, { data }, authHeaders); message.success('修改成功'); setEditRow(null); loadRows(); } catch (e) { message.error(e?.response?.data?.detail || '修改失败'); } }}>
      <Input.TextArea value={jsonText} onChange={(e) => setJsonText(e.target.value)} rows={10} />
    </Modal>
  </Card>;
}

function MergeBillBox({ orderIds, authHeaders, reload }) {
  const [price, setPrice] = useState(1);
  return <Space style={{ marginTop: 8 }}><InputNumber min={1} value={price} onChange={(v) => setPrice(v || 1)} /><Button className='click-btn' type='primary' onClick={async () => { await api.post('/api/bills/from-orders', { order_ids: orderIds, sale_unit_price: price }, authHeaders); message.success('已合并生成新账单'); reload(); }}>合并选中订单生成账单</Button></Space>;
}

function AdminBills({ role, authHeaders, bills, customers, allocations, reload }) {
  const [c, setC] = useState(); const [ids, setIds] = useState(''); const [price, setPrice] = useState(1); const [bid, setBid] = useState(); const [act, setAct] = useState('pay');
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailRows, setDetailRows] = useState([]);
  const stageLabel = (b) => {
    if (b.status === 'archived') return '已归档';
    if (b.shipping_status === 'delivered') return '已收货';
    if (b.shipping_status === 'shipped') return '已发货';
    if (b.payment_status === 'received') return '已确认支付';
    if (b.payment_status === 'paid') return '已支付';
    return '已创建';
  };
  const activeBills = bills.filter(b => b.status !== 'archived').map(b => ({ ...b, customer_name: customers.find(cu => cu.id === b.customer_id)?.name || `客户${b.customer_id}` }));
  const actionOptions = role === 'customer'
    ? [{ label: '已支付', value: 'pay' }, { label: '已收货', value: 'deliver' }]
    : [{ label: '已创建', value: 'created' }, { label: '已支付', value: 'pay' }, { label: '已确认支付', value: 'confirm_receipt' }, { label: '已发货', value: 'ship' }, { label: '已收货', value: 'deliver' }, { label: '已归档', value: 'archive' }];

  return <Card className='panel' title='账单管理'>
    {role === 'super_admin' && <Space><Select placeholder='客户' style={{ width: 180 }} options={customers.map(x => ({ label: x.name, value: x.id }))} onChange={setC} /><Input placeholder='分配ID 例 1,2' style={{ width: 220 }} value={ids} onChange={(e) => setIds(e.target.value)} /><InputNumber min={1} value={price} onChange={(v) => setPrice(v || 1)} /><Button className='click-btn' onClick={async () => { await api.post('/api/bills', { customer_id: c, allocation_ids: ids.split(',').map(s => Number(s.trim())).filter(Boolean), sale_unit_price: price }, authHeaders); message.success('账单生成成功'); reload(); }}>生成账单</Button></Space>}
    <Space style={{ marginTop: 8 }}><Select placeholder='选择账单' style={{ width: 180 }} options={activeBills.map(b => ({ label: b.bill_no, value: b.id }))} onChange={setBid} /><Select style={{ width: 220 }} value={act} onChange={setAct} options={actionOptions} /><Button className='click-btn' onClick={async () => { try { await api.post(`/api/bills/${bid}/state`, { action: act }, authHeaders); message.success('状态更新成功'); reload(); } catch (e) { message.error(e?.response?.data?.detail || '状态更新失败'); } }}>状态推进</Button></Space>
    <Table rowKey='id' dataSource={activeBills} columns={[
      { title: '账单号', dataIndex: 'bill_no' },
      { title: '账单日期', dataIndex: 'created_at', render: (v) => { const d = v ? new Date(v) : null; if (!d || Number.isNaN(d.getTime())) return '-'; const y = d.getFullYear(); const m = String(d.getMonth() + 1).padStart(2, '0'); const day = String(d.getDate()).padStart(2, '0'); return `${y}年${m}月${day}日`; } },
      ...(role === 'super_admin' ? [{ title: '客户名', dataIndex: 'customer_name' }] : []),
      { title: '金额', dataIndex: 'total_amount' },
      { title: '货品点数', dataIndex: 'goods_points' },
      { title: '账单状态', render: (_, r) => stageLabel(r) },
      { title: '操作', render: (_, r) => <Button className='click-btn' onClick={async () => { const res = await api.get(`/api/bills/${r.id}/lines`, authHeaders); setDetailRows(res.data || []); setDetailOpen(true); }}>账单详情</Button> },
    ]} style={{ marginTop: 8 }} />
    <Modal open={detailOpen} title='账单详情' footer={null} onCancel={() => setDetailOpen(false)} width={900}>
      <Table rowKey='id' pagination={false} dataSource={detailRows} columns={[
        { title: 'JAN', dataIndex: 'jan_snapshot' },
        { title: '品名', dataIndex: 'item_name_snapshot' },
        { title: '数量', dataIndex: 'qty' },
        { title: '出售单价', dataIndex: 'sale_unit_price' },
        { title: '小计价格', dataIndex: 'line_amount' },
        { title: '订货时间', dataIndex: 'order_date', render: (v) => { const d = v ? new Date(v) : null; if (!d || Number.isNaN(d.getTime())) return '-'; const y = d.getFullYear(); const m = String(d.getMonth() + 1).padStart(2, '0'); const day = String(d.getDate()).padStart(2, '0'); return `${y}年${m}月${day}日`; } },
        { title: '到货时间', dataIndex: 'arrival_date', render: (v) => { const d = v ? new Date(v) : null; if (!d || Number.isNaN(d.getTime())) return '-'; const y = d.getFullYear(); const m = String(d.getMonth() + 1).padStart(2, '0'); const day = String(d.getDate()).padStart(2, '0'); return `${y}年${m}月${day}日`; } },
      ]} />
    </Modal>
  </Card>;
}

function HistoryBillsPanel({ role, bills, customers, authHeaders }) {
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailRows, setDetailRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const rows = bills.filter(b => b.status === 'archived').map(b => ({ ...b, customer_name: customers.find(cu => cu.id === b.customer_id)?.name || `客户${b.customer_id}` }));
  const fmt = (v) => {
    const d = v ? new Date(v) : null;
    if (!d || Number.isNaN(d.getTime())) return '-';
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hh = String(d.getHours()).padStart(2, '0');
    const mm = String(d.getMinutes()).padStart(2, '0');
    return `${y}-${m}-${day} ${hh}:${mm}`;
  };
  return <Card className='panel' title='历史账单'>
    <Table rowKey='id' dataSource={rows} columns={[
      { title: '账单号', dataIndex: 'bill_no' },
      { title: '账单金额', dataIndex: 'total_amount' },
      { title: '客户', dataIndex: 'customer_name' },
      { title: '归档时间', dataIndex: 'archived_at', render: fmt },
      { title: '操作', render: (_, r) => <Button className='click-btn' loading={loading} onClick={async () => { setLoading(true); try { const res = await api.get(`/api/bills/${r.id}/lines`, authHeaders); setDetailRows(res.data || []); setDetailOpen(true); } finally { setLoading(false); } }}>查看账单明细</Button> },
    ]} />
    <Modal open={detailOpen} title='账单明细' footer={null} onCancel={() => setDetailOpen(false)} width={760}>
      <Table rowKey='id' pagination={false} dataSource={detailRows} columns={[
        { title: 'JAN', dataIndex: 'jan_snapshot' },
        { title: '商品名', dataIndex: 'item_name_snapshot' },
        { title: '数量', dataIndex: 'qty' },
        { title: '单价', dataIndex: 'sale_unit_price' },
        { title: '金额', dataIndex: 'line_amount' },
      ]} />
    </Modal>
  </Card>;
}
