import os
from datetime import datetime, time
from sqlalchemy.orm import Session
from database import now
from models import Product, ProductPrice
from . import audit_service as audit
from .errors import BusinessError, NotFound

# Janela opcional para REGISTRAR alteração de preço. Vazio (padrão) = qualquer horário.
# Para restringir: PRICE_WINDOW_START=06:00 PRICE_WINDOW_END=08:00
PRICE_WINDOW_START = os.getenv("PRICE_WINDOW_START", "")
PRICE_WINDOW_END = os.getenv("PRICE_WINDOW_END", "")


def in_price_window(at: datetime | None = None) -> bool:
    if not PRICE_WINDOW_START or not PRICE_WINDOW_END:
        return True
    at = at or now()
    start, end = time.fromisoformat(PRICE_WINDOW_START), time.fromisoformat(PRICE_WINDOW_END)
    t = at.time()
    return start <= t <= end if start <= end else (t >= start or t <= end)


def current_price(db: Session, product_id: int, at: datetime | None = None) -> int | None:
    at = at or now()
    row = (db.query(ProductPrice)
           .filter(ProductPrice.product_id == product_id, ProductPrice.effective_from <= at)
           .order_by(ProductPrice.effective_from.desc(), ProductPrice.id.desc()).first())
    return row.price_cents if row else None


def set_price(db: Session, product_id: int, price_cents: int,
              effective_from: datetime | None, user: str) -> ProductPrice:
    if not in_price_window():
        raise BusinessError(
            f"Alteração de preço só é permitida entre {PRICE_WINDOW_START} e {PRICE_WINDOW_END}", 403)
    if not db.get(Product, product_id):
        raise NotFound("Produto")
    before = current_price(db, product_id)
    price = ProductPrice(product_id=product_id, price_cents=price_cents,
                         effective_from=effective_from or now(), created_by=user)
    db.add(price)
    db.flush()
    audit.log(db, "product_price", product_id, "PRICE_CHANGE",
              {"price_cents": before}, {"price_cents": price_cents,
                                         "effective_from": str(price.effective_from)}, user)
    db.commit()
    return price
