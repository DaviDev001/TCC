from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from database import Base, now


class CashSession(Base):
    __tablename__ = "cash_sessions"
    id = Column(Integer, primary_key=True)
    user = Column(String)
    opened_at = Column(DateTime, default=now)
    closed_at = Column(DateTime, nullable=True)
    opening_cents = Column(Integer, default=0)
    closing_cents = Column(Integer, nullable=True)


class Sale(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True)
    idempotency_key = Column(String, unique=True, index=True)
    cash_session_id = Column(Integer, ForeignKey("cash_sessions.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    total_cents = Column(Integer, default=0)
    discount_cents = Column(Integer, default=0)
    change_cents = Column(Integer, default=0)   # troco
    status = Column(String, default="COMPLETED")  # COMPLETED | CANCELED
    created_by = Column(String)
    created_at = Column(DateTime, default=now)
    items = relationship("SaleItem", cascade="all, delete-orphan")
    payments = relationship("Payment", cascade="all, delete-orphan")


class SaleItem(Base):
    __tablename__ = "sale_items"
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    qty = Column(Numeric(12, 3), nullable=False)
    unit_price_cents = Column(Integer, nullable=False)  # snapshot do preço na hora da venda
    total_cents = Column(Integer, nullable=False)


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    method = Column(String, nullable=False)  # PIX|CREDIT|DEBIT|CASH|CHECK|INSTALLMENT
    amount_cents = Column(Integer, nullable=False)
    details = Column(JSON, default=dict)     # NSU/bandeira, dados do cheque, parcelas do carnê
