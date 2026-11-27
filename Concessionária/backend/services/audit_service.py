import json
from sqlalchemy.orm import Session
from models import AuditLog


def snapshot(obj) -> dict:
    data = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
    return json.loads(json.dumps(data, default=str))


def log(db: Session, entity: str, entity_id: int, action: str, before, after, user: str):
    db.add(AuditLog(entity=entity, entity_id=entity_id, action=action,
                    before=before, after=after, user=user))
