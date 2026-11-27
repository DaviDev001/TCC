from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from database import Base, now


class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    document = Column(String)   # CNPJ/CPF
    phone = Column(String)


class Purchase(Base):
    __tablename__ = "purchases"
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    invoice_number = Column(String)
    total_cents = Column(Integer, default=0)
    received_at = Column(DateTime, default=now)
    created_by = Column(String)
    items = relationship("PurchaseItem", cascade="all, delete-orphan")


class PurchaseItem(Base):
    __tablename__ = "purchase_items"
    id = Column(Integer, primary_key=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    qty = Column(Numeric(12, 3), nullable=False)
    unit_cost_cents = Column(Integer, nullable=False)
