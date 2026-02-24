from datetime import datetime
from pydantic import BaseModel


class CustomerIn(BaseModel):
    name: str


class ItemIn(BaseModel):
    jan: str
    brand: str
    name: str
    spec: str | None = None
    msrp_price: float = 0


class OrderIn(BaseModel):
    customer_id: int
    item_id: int
    qty_requested: int


class LotIn(BaseModel):
    item_id: int
    qty_received: int
    location: str | None = None


class AllocateIn(BaseModel):
    order_line_id: int
    allocated_by: str = "sales_admin"


class BuildBillIn(BaseModel):
    customer_id: int
    allocation_ids: list[int]
    sale_unit_price: float


class StateActionIn(BaseModel):
    action: str


class BasicOut(BaseModel):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
