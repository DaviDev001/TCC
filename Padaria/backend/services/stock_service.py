from decimal import Decimal
from sqlalchemy.orm import Session
from models import Product, StockMovement
from .errors import NotFound


def move(db: Session, product_id: int, qty_delta: Decimal, type_: str,
         ref_type: str | None = None, ref_id: int | None = None):
    """Registra a movimentação E atualiza o saldo na mesma transação.
    with_for_update trava a linha no Postgres e evita corrida entre dois caixas."""
    product = db.query(Product).filter(Product.id == product_id).with_for_update().first()
    if not product:
        raise NotFound("Produto")
    product.stock_balance = (product.stock_balance or Decimal(0)) + Decimal(qty_delta)
    db.add(StockMovement(product_id=product_id, qty_delta=qty_delta, type=type_,
                         ref_type=ref_type, ref_id=ref_id))
    return product
