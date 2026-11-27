from datetime import timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db, now
from models import Lead, TestDrive, Vehicle
from schemas.crm import LeadIn, LeadPatch, TestDriveIn, TestDrivePatch
from services.errors import BusinessError, NotFound

router = APIRouter(tags=["leads e test-drive"])


def _lead(db, l: Lead) -> dict:
    v = db.get(Vehicle, l.vehicle_id) if l.vehicle_id else None
    return {"id": l.id, "name": l.name, "phone": l.phone, "email": l.email, "source": l.source,
            "vehicle_id": l.vehicle_id, "vehicle": v.desc if v else None, "seller_id": l.seller_id,
            "status": l.status, "notes": l.notes, "lost_reason": l.lost_reason, "created_at": l.created_at}


@router.post("/leads", status_code=201)
def create_lead(data: LeadIn, db: Session = Depends(get_db)):
    l = Lead(**data.model_dump())
    db.add(l)
    db.commit()
    return _lead(db, l)


@router.get("/leads")
def list_leads(db: Session = Depends(get_db)):
    return [_lead(db, l) for l in db.query(Lead).order_by(Lead.updated_at.desc())]


@router.patch("/leads/{lid}")
def patch_lead(lid: int, data: LeadPatch, db: Session = Depends(get_db)):
    l = db.get(Lead, lid)
    if not l:
        raise NotFound("Lead")
    if l.status == "GANHO":
        raise BusinessError("Lead já convertido em venda", 409)
    if data.status == "PERDIDO" and not (data.lost_reason or l.lost_reason):
        raise BusinessError("Informe o motivo da perda")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(l, k, v)
    db.commit()
    return _lead(db, l)


def _drive(db, t: TestDrive) -> dict:
    v = db.get(Vehicle, t.vehicle_id)
    return {"id": t.id, "vehicle_id": t.vehicle_id, "vehicle": v.desc if v else "?",
            "customer_name": t.customer_name, "phone": t.phone, "seller_id": t.seller_id,
            "scheduled_at": t.scheduled_at, "status": t.status}


@router.post("/test-drives", status_code=201)
def schedule(data: TestDriveIn, db: Session = Depends(get_db)):
    v = db.get(Vehicle, data.vehicle_id)
    if not v:
        raise NotFound("Veículo")
    if v.status in ("VENDIDO", "BAIXADO"):
        raise BusinessError("Veículo indisponível para test-drive", 409)
    if data.scheduled_at < now():
        raise BusinessError("Horário no passado")
    gap = timedelta(minutes=60)
    clash = db.query(TestDrive).filter(
        TestDrive.vehicle_id == v.id, TestDrive.status == "AGENDADO",
        TestDrive.scheduled_at > data.scheduled_at - gap,
        TestDrive.scheduled_at < data.scheduled_at + gap).first()
    if clash:
        raise BusinessError("Já existe test-drive deste veículo em horário conflitante (intervalo de 1h)", 409)
    t = TestDrive(**data.model_dump())
    db.add(t)
    db.commit()
    return _drive(db, t)


@router.get("/test-drives")
def list_drives(db: Session = Depends(get_db)):
    return [_drive(db, t) for t in db.query(TestDrive).order_by(TestDrive.scheduled_at.desc()).limit(100)]


@router.patch("/test-drives/{tid}")
def patch_drive(tid: int, data: TestDrivePatch, db: Session = Depends(get_db)):
    t = db.get(TestDrive, tid)
    if not t:
        raise NotFound("Test-drive")
    t.status = data.status
    db.commit()
    return _drive(db, t)
