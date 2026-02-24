from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate


def create_customer(db: Session, data: CustomerCreate) -> Customer:
    obj = Customer(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_customers(db: Session):
    return db.query(Customer).order_by(Customer.id.desc()).all()