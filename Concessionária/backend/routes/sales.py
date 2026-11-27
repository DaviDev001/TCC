from datetime import date, datetime, time, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Customer, Sale, Seller, Vehicle
from schemas.sale import SaleIn
from services import dashboard_service, sale_service
from .deps import current_user

router = APIRouter(tags=["vendas e dashboard"])


def _out(db, s: Sale) -> dict:
    v, c, sl = db.get(Vehicle, s.vehicle_id), db.get(Customer, s.customer_id), db.get(Seller, s.seller_id)
    return {"id": s.id, "status": s.status, "created_at": s.created_at,
            "vehicle": v.desc if v else "?", "plate": v.plate if v else None,
            "customer": c.name if c else "?", "seller": sl.name if sl else "?",
            "list_price_cents": s.list_price_cents, "discount_cents": s.discount_cents,
            "final_cents": s.final_cents, "cost_cents": s.cost_cents,
            "profit_cents": s.profit_cents, "commission_cents": s.commission_cents,
            "approved_by": s.approved_by,
            "payments": [{"method": p.method, "amount_cents": p.amount_cents, "details": p.details}
                         for p in s.payments]}


@router.post("/sales", status_code=201)
def create(data: SaleIn, db: Session = Depends(get_db), user: str = Depends(current_user)):
    return _out(db, sale_service.create_sale(db, data, user))


@router.get("/sales")
def list_sales(month: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Sale)
    if month:
        first = date.fromisoformat(month + "-01")
        nxt = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
        q = q.filter(Sale.created_at >= datetime.combine(first, time.min),
                     Sale.created_at < datetime.combine(nxt, time.min))
    return [_out(db, s) for s in q.order_by(Sale.id.desc())]


@router.post("/sales/{sid}/cancel")
def cancel(sid: int, db: Session = Depends(get_db), user: str = Depends(current_user)):
    return _out(db, sale_service.cancel_sale(db, sid, user))


@router.get("/dashboard")
def dashboard(month: str | None = None, db: Session = Depends(get_db)):
    return dashboard_service.build(db, month)
