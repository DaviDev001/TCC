from sqlalchemy.orm import Session
from models import Product
from schemas.product import ProductIn, ProductUpdate
from . import audit_service as audit
from .errors import NotFound


def create_product(db: Session, data: ProductIn, user: str) -> Product:
    p = Product(**data.model_dump())
    db.add(p)
    db.flush()
    audit.log(db, "product", p.id, "CREATE", None, audit.snapshot(p), user)
    db.commit()
    return p


def update_product(db: Session, product_id: int, data: ProductUpdate, user: str) -> Product:
    p = db.get(Product, product_id)
    if not p:
        raise NotFound("Produto")
    before = audit.snapshot(p)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    audit.log(db, "product", p.id, "UPDATE", before, audit.snapshot(p), user)
    db.commit()
    return p
