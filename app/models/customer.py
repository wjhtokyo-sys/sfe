from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False, comment="客户名称")
    phone = Column(String(50), nullable=True, comment="电话")
    email = Column(String(100), nullable=True, comment="邮箱")
    note = Column(String(255), nullable=True, comment="备注")

    created_at = Column(DateTime, default=datetime.utcnow)