from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Product, ProductPrice
from schemas.product import (PriceIn, PriceOut, ProductIn, ProductOut, ProductUpdate,
                             StockAdjustIn)
from services import audit_service as audit, price_service, product_service, stock_service
from services.errors import NotFound
from .deps import current_user

router = APIRouter(tags=["produtos"])


def _out(db, p: Product) -> ProductOut:
    out = ProductOut.model_validate(p)
    out.current_price_cents = price_service.current_price(db, p.id)
    return out


@router.post("/products", response_model=ProductOut, status_code=201)
def create(data: ProductIn, db: Session = Depends(get_db), user: str = Depends(current_user)):
    return _out(db, product_service.create_product(db, data, user))


@router.get("/products", response_model=list[ProductOut])
def list_products(active: bool = True, db: Session = Depends(get_db)):
    return [_out(db, p) for p in db.query(Product).filter_by(active=active).order_by(Product.name)]


@router.get("/products/barcode/{code}", response_model=ProductOut)
def by_barcode(code: str, db: Session = Depends(get_db)):
    p = db.query(Product).filter_by(barcode=code, active=True).first()
    if not p:
        raise NotFound("Produto")
    return _out(db, p)


@router.put("/products/{product_id}", response_model=ProductOut)
def update(product_id: int, data: ProductUpdate, db: Session = Depends(get_db),
           user: str = Depends(current_user)):
    return _out(db, product_service.update_product(db, product_id, data, user))


@router.post("/products/{product_id}/prices", response_model=PriceOut, status_code=201)
def set_price(product_id: int, data: PriceIn, db: Session = Depends(get_db),
              user: str = Depends(current_user)):
    return price_service.set_price(db, product_id, data.price_cents, data.effective_from, user)


@router.get("/products/{product_id}/prices", response_model=list[PriceOut])
def price_history(product_id: int, db: Session = Depends(get_db)):
    return (db.query(ProductPrice).filter_by(product_id=product_id)
            .order_by(ProductPrice.effective_from.desc()).all())


@router.get("/stock", response_model=list[ProductOut])
def stock(db: Session = Depends(get_db)):
    return [_out(db, p) for p in db.query(Product).order_by(Product.stock_balance)]


@router.post("/stock/adjustments", status_code=201)
def adjust(data: StockAdjustIn, db: Session = Depends(get_db), user: str = Depends(current_user)):
    p = stock_service.move(db, data.product_id, data.qty_delta, data.type, "adjustment", None)
    audit.log(db, "stock", p.id, data.type, None,
              {"qty_delta": str(data.qty_delta), "reason": data.reason}, user)
    db.commit()
    return {"product_id": p.id, "stock_balance": str(p.stock_balance)}
