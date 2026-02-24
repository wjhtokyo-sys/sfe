import React, { useEffect } from 'react';
import { Button, Card, Col, Form, Input, InputNumber, Row, Space, Table, Tag, Typography } from 'antd';
import { useDispatch, useSelector } from 'react-redux';
import { loadDashboard } from './features/sfeSlice';
import { api } from './api/client';

const { Title } = Typography;

export default function App() {
  const dispatch = useDispatch();
  const data = useSelector((s) => s.sfe);

  useEffect(() => { dispatch(loadDashboard()); }, [dispatch]);

  const refresh = () => dispatch(loadDashboard());

  const quick = async (path, payload) => { await api.post(path, payload); refresh(); };

  return (
    <div style={{ padding: 16 }}>
      <Title level={3}>SFE 业务闭环看板</Title>
      <Space wrap>
        <Card title='创建客户'>
          <Form onFinish={(v) => quick('/customers', v)} layout='inline'>
            <Form.Item name='name' rules={[{ required: true }]}><Input placeholder='客户名' /></Form.Item>
            <Button htmlType='submit' type='primary'>新增</Button>
          </Form>
        </Card>
        <Card title='创建商品'>
          <Form onFinish={(v) => quick('/items', v)} layout='inline'>
            <Form.Item name='jan' rules={[{ required: true }]}><Input placeholder='JAN' /></Form.Item>
            <Form.Item name='brand' rules={[{ required: true }]}><Input placeholder='品牌' /></Form.Item>
            <Form.Item name='name' rules={[{ required: true }]}><Input placeholder='商品名' /></Form.Item>
            <Button htmlType='submit' type='primary'>新增</Button>
          </Form>
        </Card>
      </Space>

      <Row gutter={12} style={{ marginTop: 16 }}>
        <Col span={12}><SimpleTable title='订单' data={data.orders} cols={['id','customer_id','item_name_snapshot','qty_requested','qty_allocated','status']} /></Col>
        <Col span={12}><SimpleTable title='库存批次' data={data.lots} cols={['id','item_id','qty_received','qty_remaining','fifo_rank']} /></Col>
      </Row>

      <Row gutter={12} style={{ marginTop: 16 }}>
        <Col span={8}><ActionCard title='创建订单' onFinish={(v)=>quick('/orders', v)} fields={[['customer_id'],['item_id'],['qty_requested']]} /></Col>
        <Col span={8}><ActionCard title='到货入库' onFinish={(v)=>quick('/lots', v)} fields={[['item_id'],['qty_received']]} /></Col>
        <Col span={8}><ActionCard title='FIFO分配' onFinish={(v)=>quick('/allocations/fifo', v)} fields={[['order_line_id']]} /></Col>
      </Row>

      <Row gutter={12} style={{ marginTop: 16 }}>
        <Col span={12}><ActionCard title='生成账单' onFinish={(v)=>quick('/bills', {...v, allocation_ids: String(v.allocation_ids).split(',').map(Number)})} fields={[['customer_id'],['allocation_ids','逗号分隔 allocation id'],['sale_unit_price']]} /></Col>
        <Col span={12}><ActionCard title='账单状态推进' onFinish={(v)=>quick(`/bills/${v.bill_id}/state`, {action:v.action})} fields={[['bill_id'],['action','pay/confirm_receipt/ship/deliver/archive']]} /></Col>
      </Row>

      <Row gutter={12} style={{ marginTop: 16 }}>
        <Col span={12}><SimpleTable title='分配记录' data={data.allocations} cols={['id','order_line_id','lot_id','qty_allocated','status']} /></Col>
        <Col span={12}><SimpleTable title='账单' data={data.bills} cols={['id','bill_no','status','payment_status','shipping_status','total_amount']} /></Col>
      </Row>
    </div>
  );
}

function ActionCard({ title, onFinish, fields }) {
  return <Card title={title}><Form onFinish={onFinish} layout='vertical'>{fields.map(([name, p]) => (
    <Form.Item key={name} name={name} label={name} rules={[{ required: true }]}>
      {name.includes('action') || name.includes('allocation_ids') ? <Input placeholder={p || ''} /> : <InputNumber style={{ width: '100%' }} placeholder={p || ''} />}
    </Form.Item>))}<Button htmlType='submit' type='primary'>执行</Button></Form></Card>;
}

function SimpleTable({ title, data, cols }) {
  const columns = cols.map((k)=>({title:k,dataIndex:k,key:k,render:(v)=>k==='status'?<Tag>{v}</Tag>:v}));
  return <Card title={title}><Table rowKey='id' columns={columns} dataSource={data} size='small' pagination={{ pageSize: 5 }} /></Card>;
}
