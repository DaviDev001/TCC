from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Supplier
from schemas.purchase import PurchaseIn, PurchaseOut, SupplierIn, SupplierOut
from services import purchase_service
from .deps import current_user

router = APIRouter(tags=["fornecedores e compras"])


@router.post("/suppliers", response_model=SupplierOut, status_code=201)
def create_supplier(data: SupplierIn, db: Session = Depends(get_db)):
    s = Supplier(**data.model_dump())
    db.add(s)
    db.commit()
    return s


@router.get("/suppliers", response_model=list[SupplierOut])
def list_suppliers(db: Session = Depends(get_db)):
    return db.query(Supplier).order_by(Supplier.name).all()


@router.post("/purchases", response_model=PurchaseOut, status_code=201)
def receive(data: PurchaseIn, db: Session = Depends(get_db), user: str = Depends(current_user)):
    return purchase_service.receive_purchase(db, data, user)
