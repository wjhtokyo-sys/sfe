import os

from fastapi.testclient import TestClient
from main import app
from seed import run as seed_run

if os.getenv('SFE_ENV', '').strip().lower() in {'prod', 'production'}:
    raise RuntimeError('tests/test_flow.py 禁止在生产环境执行')

client = TestClient(app)


def admin_headers():
    login = client.post('/auth/admin-login', json={'username': 'admin1', 'password': 'admin123'})
    token = login.json()['token']
    return {'Authorization': f'Bearer {token}'}


def customer_headers(username='cust1'):
    login = client.post('/auth/customer-login', json={'username': username, 'password': '123456'})
    token = login.json()['token']
    return {'Authorization': f'Bearer {token}'}


def test_full_flow_and_state_guard():
    seed_run()
    h = admin_headers()

    c = client.get('/api/customers', headers=h).json()[0]
    i = client.get('/api/items', headers=h).json()[0]

    o = client.post('/api/orders', json={'customer_id': c['id'], 'item_id': i['id'], 'qty_requested': 5}, headers=h).json()
    client.post('/api/lots', json={'item_id': i['id'], 'qty_received': 3}, headers=h)
    client.post('/api/lots', json={'item_id': i['id'], 'qty_received': 4}, headers=h)

    allocs = client.post('/api/allocations/fifo', json={'order_line_id': o['id']}, headers=h).json()
    alloc_ids = [a['id'] for a in allocs]

    bill = client.post('/api/bills', json={'customer_id': c['id'], 'allocation_ids': alloc_ids, 'sale_unit_price': 20}, headers=h).json()

    bad = client.post(f"/api/bills/{bill['id']}/state", json={'action': 'deliver'}, headers=h)
    assert bad.status_code == 400

    assert client.post(f"/api/bills/{bill['id']}/state", json={'action': 'pay'}, headers=h).status_code == 200


def test_customer_cannot_access_admin_data():
    seed_run()
    h = customer_headers('cust1')
    assert client.get('/api/customers', headers=h).status_code == 403
