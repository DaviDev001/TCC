from sqlalchemy import JSON, Column, DateTime, Integer, String
from database import Base, now


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    entity = Column(String, index=True)
    entity_id = Column(Integer, index=True)
    action = Column(String)
    before = Column(JSON, nullable=True)
    after = Column(JSON, nullable=True)
    user = Column(String)
    created_at = Column(DateTime, default=now, index=True)
