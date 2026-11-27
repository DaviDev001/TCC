from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String
from database import Base, now


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    document = Column(String)
    phone = Column(String)
    credit_limit_cents = Column(Integer, default=0)


class Receivable(Base):
    """Parcela de carnê (venda a prazo)."""
    __tablename__ = "receivables"
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True)
    installment_no = Column(Integer)
    due_date = Column(Date)
    amount_cents = Column(Integer)
    paid_cents = Column(Integer, default=0)
    status = Column(String, default="OPEN")  # OPEN | PAID | CANCELED


class ReceivablePayment(Base):
    __tablename__ = "receivable_payments"
    id = Column(Integer, primary_key=True)
    receivable_id = Column(Integer, ForeignKey("receivables.id"))
    amount_cents = Column(Integer)
    method = Column(String)
    cash_session_id = Column(Integer, ForeignKey("cash_sessions.id"), nullable=True)
    created_at = Column(DateTime, default=now)
