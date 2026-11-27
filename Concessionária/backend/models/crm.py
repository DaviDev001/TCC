from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from database import Base, now


class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String)
    email = Column(String)
    source = Column(String, default="LOJA")      # LOJA|SITE|INDICACAO|REDES|TELEFONE
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    seller_id = Column(Integer, ForeignKey("sellers.id"), nullable=True)
    status = Column(String, default="NOVO")      # NOVO|CONTATO|VISITA|PROPOSTA|GANHO|PERDIDO
    notes = Column(String)
    lost_reason = Column(String)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)


class TestDrive(Base):
    __tablename__ = "test_drives"
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    seller_id = Column(Integer, ForeignKey("sellers.id"), nullable=True)
    customer_name = Column(String, nullable=False)
    phone = Column(String)
    cnh = Column(String)
    scheduled_at = Column(DateTime, nullable=False)
    status = Column(String, default="AGENDADO")  # AGENDADO|REALIZADO|CANCELADO
