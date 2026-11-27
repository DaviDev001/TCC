from sqlalchemy import Boolean, Column, Integer, Numeric, String
from database import Base


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    document = Column(String, unique=True, nullable=False)   # CPF/CNPJ (só dígitos)
    phone = Column(String)
    email = Column(String)
    city = Column(String)


class Seller(Base):
    __tablename__ = "sellers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    commission_pct = Column(Numeric(5, 2), default=1.5)      # % sobre o lucro bruto da venda
    active = Column(Boolean, default=True)
