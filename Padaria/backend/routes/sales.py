from datetime import date
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import CashSession, Customer, Receivable
from schemas.sale import CashCloseIn, CashOpenIn, ReceivablePayIn, SaleIn, SaleOut
from services import sale_service
from .deps import current_user

router = APIRouter(tags=["caixa, vendas e carnê"])


@router.post("/cash-sessions/open", status_code=201)
def open_cash(data: CashOpenIn, db: Session = Depends(get_db), user: str = Depends(current_user)):
    s = sale_service.open_session(db, data.opening_cents, user)
    return {"id": s.id, "opened_at": s.opened_at}


@router.get("/cash-sessions/current")
def current_cash(db: Session = Depends(get_db), user: str = Depends(current_user)):
    s = db.query(CashSession).filter_by(user=user, closed_at=None).first()
    return {"id": s.id, "opened_at": s.opened_at, "opening_cents": s.opening_cents} if s else None


@router.post("/cash-sessions/{session_id}/close")
def close_cash(session_id: int, data: CashCloseIn, db: Session = Depends(get_db)):
    return sale_service.close_session(db, session_id, data.closing_cents)


@router.post("/sales", response_model=SaleOut, status_code=201)
def create_sale(data: SaleIn, db: Session = Depends(get_db), user: str = Depends(current_user)):
    return sale_service.create_sale(db, data, user)


@router.post("/sales/{sale_id}/cancel", response_model=SaleOut)
def cancel_sale(sale_id: int, db: Session = Depends(get_db), user: str = Depends(current_user)):
    return sale_service.cancel_sale(db, sale_id, user)


class CustomerIn(BaseModel):
    name: str
    document: str | None = None
    phone: str | None = None
    credit_limit_cents: int = 0


@router.post("/customers", status_code=201)
def create_customer(data: CustomerIn, db: Session = Depends(get_db)):
    c = Customer(**data.model_dump())
    db.add(c)
    db.commit()
    return {"id": c.id, **data.model_dump()}


@router.get("/customers")
def list_customers(db: Session = Depends(get_db)):
    return [{"id": c.id, "name": c.name, "document": c.document, "phone": c.phone,
             "credit_limit_cents": c.credit_limit_cents}
            for c in db.query(Customer).order_by(Customer.name)]


@router.get("/receivables")
def list_receivables(customer_id: int | None = None, status: str = "OPEN",
                     db: Session = Depends(get_db)):
    q = db.query(Receivable).filter_by(status=status)
    if customer_id:
        q = q.filter_by(customer_id=customer_id)
    return [{"id": r.id, "sale_id": r.sale_id, "customer_id": r.customer_id,
             "installment_no": r.installment_no, "due_date": r.due_date,
             "amount_cents": r.amount_cents, "paid_cents": r.paid_cents}
            for r in q.order_by(Receivable.due_date)]


@router.post("/receivables/{rec_id}/pay")
def pay(rec_id: int, data: ReceivablePayIn, db: Session = Depends(get_db)):
    r = sale_service.pay_receivable(db, rec_id, data.amount_cents, data.method.value,
                                    data.cash_session_id)
    return {"id": r.id, "paid_cents": r.paid_cents, "status": r.status}


@router.get("/reports/daily-closing")
def daily_closing(day: date, db: Session = Depends(get_db)):
    return sale_service.daily_closing(db, day)
