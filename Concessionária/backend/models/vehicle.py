from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base, now


class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True)
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)
    version = Column(String)
    year_fab = Column(Integer)
    year_model = Column(Integer)
    color = Column(String)
    plate = Column(String, unique=True, nullable=True)
    chassis = Column(String, unique=True, nullable=True)
    km = Column(Integer, default=0)
    fuel = Column(String, default="FLEX")
    transmission = Column(String, default="MANUAL")
    condition = Column(String, default="USADO")       # NOVO | USADO
    purchase_cents = Column(Integer, default=0)       # custo de aquisição
    price_cents = Column(Integer, default=0)          # preço anunciado
    status = Column(String, default="DISPONIVEL")     # DISPONIVEL|RESERVADO|MANUTENCAO|VENDIDO|BAIXADO
    notes = Column(String)
    created_at = Column(DateTime, default=now)
    sold_at = Column(DateTime, nullable=True)
    expenses = relationship("VehicleExpense", cascade="all, delete-orphan", order_by="VehicleExpense.id")

    @property
    def expenses_cents(self) -> int:
        return sum(e.amount_cents for e in self.expenses)

    @property
    def cost_cents(self) -> int:       # custo total = compra + preparação/despesas
        return (self.purchase_cents or 0) + self.expenses_cents

    @property
    def desc(self) -> str:
        return f"{self.brand} {self.model} {self.version or ''} {self.year_model}".replace("  ", " ").strip()


class VehicleExpense(Base):
    __tablename__ = "vehicle_expenses"
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), index=True)
    description = Column(String, nullable=False)
    amount_cents = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=now)
