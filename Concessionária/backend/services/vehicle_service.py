from sqlalchemy.orm import Session
from database import now
from models import Vehicle, VehicleExpense
from schemas.vehicle import ExpenseIn, StatusIn, VehicleIn, VehicleUpdate
from . import audit_service as audit
from .errors import BusinessError, NotFound


def get(db: Session, vid: int) -> Vehicle:
    v = db.get(Vehicle, vid)
    if not v:
        raise NotFound("Veículo")
    return v


def create(db: Session, data: VehicleIn, user: str) -> Vehicle:
    v = Vehicle(**data.model_dump())
    db.add(v)
    db.flush()
    audit.log(db, "vehicle", v.id, "CREATE", None, audit.snapshot(v), user)
    db.commit()
    return v


def update(db: Session, vid: int, data: VehicleUpdate, user: str) -> Vehicle:
    v = get(db, vid)
    if v.status == "VENDIDO":
        raise BusinessError("Veículo vendido não pode ser alterado", 409)
    before = audit.snapshot(v)
    changes = data.model_dump(exclude_unset=True)
    for k, val in changes.items():
        setattr(v, k, val)
    action = "PRICE_CHANGE" if "price_cents" in changes and changes["price_cents"] != before["price_cents"] else "UPDATE"
    audit.log(db, "vehicle", v.id, action, before, audit.snapshot(v), user)
    db.commit()
    return v


def set_status(db: Session, vid: int, data: StatusIn, user: str) -> Vehicle:
    v = get(db, vid)
    if v.status == "VENDIDO":
        raise BusinessError("Veículo vendido: cancele a venda para liberar o estoque", 409)
    before = {"status": v.status}
    v.status = data.status
    audit.log(db, "vehicle", v.id, "STATUS", before, {"status": v.status}, user)
    db.commit()
    return v


def add_expense(db: Session, vid: int, data: ExpenseIn, user: str) -> Vehicle:
    v = get(db, vid)
    if v.status == "VENDIDO":
        raise BusinessError("Veículo já vendido: o custo foi fechado na venda", 409)
    v.expenses.append(VehicleExpense(**data.model_dump(), created_at=now()))
    audit.log(db, "vehicle", v.id, "EXPENSE", None, data.model_dump(), user)
    db.commit()
    return v
