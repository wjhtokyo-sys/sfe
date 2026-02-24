from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ⭐ 创建用
class CustomerCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    note: Optional[str] = None


# ⭐ 返回用
class CustomerOut(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    email: Optional[str]
    note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True  # ⭐ 兼容 SQLAlchemy