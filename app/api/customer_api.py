from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.customer import CustomerCreate, CustomerOut
from app.services.customer_service import create_customer, get_customers

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("", response_model=CustomerOut)
def create_customer_api(
    data: CustomerCreate,
    db: Session = Depends(get_db),
):
    return create_customer(db, data)


@router.get("", response_model=List[CustomerOut])
def list_customers_api(db: Session = Depends(get_db)):
    return get_customers(db)