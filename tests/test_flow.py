from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_full_flow():
    suffix = client.get('/api/customers').status_code
    c_resp = client.post('/api/customers', json={'name': 'Alice'})
    assert c_resp.status_code == 200
    c = c_resp.json()

    i_resp = client.post('/api/items', json={'jan': f'JAN-{c["id"]}', 'brand': 'Shimano', 'name': 'X1'})
    assert i_resp.status_code == 200
    i = i_resp.json()

    o_resp = client.post('/api/orders', json={'customer_id': c['id'], 'item_id': i['id'], 'qty_requested': 5})
    assert o_resp.status_code == 200
    o = o_resp.json()

    assert client.post('/api/lots', json={'item_id': i['id'], 'qty_received': 3}).status_code == 200
    assert client.post('/api/lots', json={'item_id': i['id'], 'qty_received': 4}).status_code == 200

    alloc_resp = client.post('/api/allocations/fifo', json={'order_line_id': o['id']})
    assert alloc_resp.status_code == 200
    allocs = alloc_resp.json()
    alloc_ids = [a['id'] for a in allocs]
    assert len(alloc_ids) == 2

    bill_resp = client.post('/api/bills', json={'customer_id': c['id'], 'allocation_ids': alloc_ids, 'sale_unit_price': 20})
    assert bill_resp.status_code == 200
    bill = bill_resp.json()
    assert bill['total_amount'] == 100

    paid = client.post(f"/api/bills/{bill['id']}/state", json={'action': 'pay'}).json()
    assert paid['payment_status'] == 'paid'
