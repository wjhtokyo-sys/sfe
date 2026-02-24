import React, { useEffect, useMemo, useState } from 'react';
import { Button, Card, Form, Input, Layout, Menu, Table, Typography, message } from 'antd';
import { api } from './api/client';

const { Sider, Content } = Layout;
const { Title } = Typography;

export default function App() {
  const [mode, setMode] = useState('home');
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [role, setRole] = useState(localStorage.getItem('role') || '');
  const [menu, setMenu] = useState('items');
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
      const detail = err?.response?.data?.detail || '登录失败';
      message.error(String(detail));
    }
  };

  const load = async () => {
    if (!token) return;
    const req = (u) => api.get(u, authHeaders).then((r) => r.data).catch(() => []);
    const [items, orders, bills, customers, lots, allocations] = await Promise.all([
      req('/api/items'),
      req('/api/orders'),
      req('/api/bills'),
      req('/api/customers'),
      req('/api/lots'),
      req('/api/allocations'),
    ]);
    setData({ items, orders, bills, customers, lots, allocations });
  };

  useEffect(() => {
    if (token) {
      setMode('panel');
      load();
    }
  }, [token]);

  const logout = () => {
    setToken('');
    setRole('');
    setMode('home');
    localStorage.clear();
  };

  if (mode === 'home') {
    return (
      <div className="page">
        <Title level={3}>SFE 登录入口</Title>
        <div className="login-wrap">
          <Card title="客户登录入口页">
            <Form onFinish={(v) => login('/auth/customer-login', v)}>
              <Form.Item name="username" rules={[{ required: true }]}>
                <Input placeholder="客户账号" />
              </Form.Item>
              <Form.Item name="password" rules={[{ required: true }]}>
                <Input.Password placeholder="密码" />
              </Form.Item>
              <Button className="click-btn" type="primary" htmlType="submit">
                客户登录
              </Button>
            </Form>
          </Card>
        </div>

        <div className="login-wrap">
          <Card title="管理员登录入口页">
            <Form onFinish={(v) => login('/auth/admin-login', v)}>
              <Form.Item name="username" rules={[{ required: true }]}>
                <Input placeholder="管理员账号" />
              </Form.Item>
              <Form.Item name="password" rules={[{ required: true }]}>
                <Input.Password placeholder="密码" />
              </Form.Item>
              <Button className="click-btn" type="primary" htmlType="submit">
                管理员登录
              </Button>
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

  const showTable = (title, arr) => (
    <Card className="panel" title={title}>
      <Table
        size="small"
        rowKey="id"
        dataSource={arr}
        columns={Object.keys(arr[0] || { id: 1 }).map((k) => ({ title: k, dataIndex: k, key: k }))}
      />
    </Card>
  );

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider>
        <div style={{ color: '#fff', padding: 16 }}>{role === 'customer' ? '客户管理页' : '管理员管理页'}</div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[menu]}
          items={role === 'customer' ? customerMenus : adminMenus}
          onClick={(e) => setMenu(e.key)}
        />
      </Sider>
      <Layout>
        <Content className="page">
          <Button className="click-btn" onClick={logout}>
            退出登录
          </Button>
          {menu === 'items' && showTable('商品信息查询', data.items)}
          {menu === 'orders' && showTable('订单管理', data.orders)}
          {menu === 'bills' && showTable('账单管理', data.bills)}
          {menu === 'history' && showTable('历史账单', data.bills.filter((b) => b.status === 'archived'))}
          {menu === 'customers' && showTable('客户管理', data.customers)}
          {menu === 'fifo' && (
            <>
              {showTable('FIFO库存批次', data.lots)}
              {showTable('FIFO分配记录', data.allocations)}
            </>
          )}
        </Content>
      </Layout>
    </Layout>
  );
}
