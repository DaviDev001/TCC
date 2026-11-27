from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base, now


class Sale(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    seller_id = Column(Integer, ForeignKey("sellers.id"))
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    list_price_cents = Column(Integer)      # preço anunciado na hora da venda (snapshot)
    discount_cents = Column(Integer, default=0)
    final_cents = Column(Integer)
    cost_cents = Column(Integer)            # custo do veículo na hora da venda (snapshot)
    profit_cents = Column(Integer)
    commission_cents = Column(Integer, default=0)
    approved_by = Column(String)            # gerente que aprovou desconto acima do limite
    status = Column(String, default="FECHADA")  # FECHADA | CANCELADA
    created_by = Column(String)
    created_at = Column(DateTime, default=now)
    payments = relationship("SalePayment", cascade="all, delete-orphan")


class SalePayment(Base):
    __tablename__ = "sale_payments"
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    method = Column(String, nullable=False)  # PIX|TED|DINHEIRO|CARTAO|CHEQUE|FINANCIAMENTO|TROCA
    amount_cents = Column(Integer, nullable=False)
    details = Column(JSON, default=dict)
