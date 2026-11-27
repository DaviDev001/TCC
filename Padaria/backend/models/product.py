from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from database import Base, now


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    barcode = Column(String, unique=True, nullable=True)
    unit = Column(String, default="UN")                 # UN | KG
    cost_cents = Column(Integer, default=0)
    stock_balance = Column(Numeric(12, 3), default=0)   # saldo (cache da soma das movimentações)
    active = Column(Boolean, default=True)


class ProductPrice(Base):
    """Preço com vigência: vale o registro mais recente com effective_from <= agora."""
    __tablename__ = "product_prices"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    price_cents = Column(Integer, nullable=False)
    effective_from = Column(DateTime, nullable=False, default=now)
    created_by = Column(String)
    created_at = Column(DateTime, default=now)
