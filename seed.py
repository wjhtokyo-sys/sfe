from app.core.database import SessionLocal
from app.models.entities import Customer, Item, User


def run():
    db = SessionLocal()
    try:
        if db.query(Customer).count() < 3:
            customers = [Customer(name='客户A', is_active=True), Customer(name='客户B', is_active=True), Customer(name='客户C', is_active=True)]
            db.add_all(customers)
            db.commit()
        customers = db.query(Customer).order_by(Customer.id.asc()).limit(3).all()

        if db.query(User).count() == 0:
            users = [
                User(username='cust1', password='123456', role='customer', customer_id=customers[0].id),
                User(username='cust2', password='123456', role='customer', customer_id=customers[1].id),
                User(username='cust3', password='123456', role='customer', customer_id=customers[2].id),
                User(username='super1', password='admin123', role='super_admin', customer_id=None),
                User(username='admin1', password='admin123', role='admin', customer_id=None),
            ]
            db.add_all(users)
            db.commit()

        if db.query(Item).count() < 20:
            for i in range(1, 21):
                jan = f'JAN{i:05d}'
                exists = db.query(Item).filter(Item.jan == jan).first()
                if not exists:
                    db.add(Item(jan=jan, brand='Shimano', name=f'商品{i}', msrp_price=100 + i, in_qty=1, is_active=True))
            db.commit()
    finally:
        db.close()


if __name__ == '__main__':
    run()
    print('seed done')
