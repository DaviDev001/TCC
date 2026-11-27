import json
from datetime import timedelta
from sqlalchemy.orm import Session
from database import now
from models import AuditLog

RETENTION_DAYS = 7


def snapshot(obj) -> dict:
    data = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
    return json.loads(json.dumps(data, default=str))  # Decimal/datetime -> str


def log(db: Session, entity: str, entity_id: int, action: str, before, after, user: str):
    db.add(AuditLog(entity=entity, entity_id=entity_id, action=action,
                    before=before, after=after, user=user))


def purge_old(db: Session, days: int = RETENTION_DAYS) -> int:
    """Apaga SOMENTE o log de auditoria. Vendas/estoque/financeiro nunca são apagados."""
    n = db.query(AuditLog).filter(AuditLog.created_at < now() - timedelta(days=days)).delete()
    db.commit()
    return n
