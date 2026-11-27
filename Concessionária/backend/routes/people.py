from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session
from database import get_db
from models import Customer, Seller
from schemas.people import CustomerIn, CustomerOut, SellerIn, SellerOut
from services.errors import NotFound

router = APIRouter(tags=["clientes e vendedores"])


@router.post("/customers", response_model=CustomerOut, status_code=201)
def create_customer(data: CustomerIn, db: Session = Depends(get_db)):
    c = Customer(**data.model_dump())
    db.add(c)
    db.commit()
    return c


@router.get("/customers", response_model=list[CustomerOut])
def list_customers(q: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Customer)
    if q:
        query = query.filter(or_(Customer.name.ilike(f"%{q}%"), Customer.document.like(f"%{q}%")))
    return query.order_by(Customer.name).all()


@router.put("/customers/{cid}", response_model=CustomerOut)
def update_customer(cid: int, data: CustomerIn, db: Session = Depends(get_db)):
    c = db.get(Customer, cid)
    if not c:
        raise NotFound("Cliente")
    for k, v in data.model_dump().items():
        setattr(c, k, v)
    db.commit()
    return c


@router.post("/sellers", response_model=SellerOut, status_code=201)
def create_seller(data: SellerIn, db: Session = Depends(get_db)):
    s = Seller(**data.model_dump())
    db.add(s)
    db.commit()
    return s


@router.get("/sellers", response_model=list[SellerOut])
def list_sellers(db: Session = Depends(get_db)):
    return db.query(Seller).order_by(Seller.name).all()


@router.patch("/sellers/{sid}/toggle", response_model=SellerOut)
def toggle_seller(sid: int, db: Session = Depends(get_db)):
    s = db.get(Seller, sid)
    if not s:
        raise NotFound("Vendedor")
    s.active = not s.active
    db.commit()
    return s
