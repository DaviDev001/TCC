from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session
from database import get_db
from models import AuditLog, Vehicle
from schemas.vehicle import ExpenseIn, StatusIn, VehicleIn, VehicleOut, VehicleUpdate
from services import vehicle_service as svc
from .deps import current_user

router = APIRouter(tags=["veículos"])


@router.post("/vehicles", response_model=VehicleOut, status_code=201)
def create(data: VehicleIn, db: Session = Depends(get_db), user: str = Depends(current_user)):
    return svc.create(db, data, user)


@router.get("/vehicles", response_model=list[VehicleOut])
def list_vehicles(status: str | None = None, q: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Vehicle)
    if status:
        query = query.filter(Vehicle.status == status)
    else:
        query = query.filter(Vehicle.status.notin_(["BAIXADO"]))
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Vehicle.brand.ilike(like), Vehicle.model.ilike(like),
                                 Vehicle.plate.ilike(like), Vehicle.color.ilike(like)))
    return query.order_by(Vehicle.created_at.desc()).all()


@router.get("/vehicles/{vid}", response_model=VehicleOut)
def detail(vid: int, db: Session = Depends(get_db)):
    return svc.get(db, vid)


@router.put("/vehicles/{vid}", response_model=VehicleOut)
def update(vid: int, data: VehicleUpdate, db: Session = Depends(get_db), user: str = Depends(current_user)):
    return svc.update(db, vid, data, user)


@router.patch("/vehicles/{vid}/status", response_model=VehicleOut)
def status(vid: int, data: StatusIn, db: Session = Depends(get_db), user: str = Depends(current_user)):
    return svc.set_status(db, vid, data, user)


@router.post("/vehicles/{vid}/expenses", response_model=VehicleOut, status_code=201)
def expense(vid: int, data: ExpenseIn, db: Session = Depends(get_db), user: str = Depends(current_user)):
    return svc.add_expense(db, vid, data, user)


@router.get("/vehicles/{vid}/history")
def history(vid: int, db: Session = Depends(get_db)):
    rows = (db.query(AuditLog).filter_by(entity="vehicle", entity_id=vid)
            .order_by(AuditLog.id.desc()).all())
    return [{"action": r.action, "user": r.user, "at": r.created_at,
             "before": r.before, "after": r.after} for r in rows]
