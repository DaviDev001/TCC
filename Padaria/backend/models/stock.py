from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from database import Base, now


class StockMovement(Base):
    __tablename__ = "stock_movements"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    qty_delta = Column(Numeric(12, 3), nullable=False)
    type = Column(String, nullable=False)  # PURCHASE | SALE | SALE_CANCEL | ADJUSTMENT | LOSS
    ref_type = Column(String)
    ref_id = Column(Integer)
    created_at = Column(DateTime, default=now)
