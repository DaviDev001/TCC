from sqlalchemy.orm import Session
from models import Product, Purchase, PurchaseItem, Supplier
from schemas.purchase import PurchaseIn
from . import audit_service as audit, stock_service
from .errors import BusinessError, NotFound


def receive_purchase(db: Session, data: PurchaseIn, user: str) -> Purchase:
    if not db.get(Supplier, data.supplier_id):
        raise NotFound("Fornecedor")
    purchase = Purchase(supplier_id=data.supplier_id,
                        invoice_number=data.invoice_number, created_by=user)
    total = 0
    for it in data.items:
        product = db.get(Product, it.product_id)
        if not product:
            raise BusinessError(f"Produto {it.product_id} não existe", 404)
        purchase.items.append(PurchaseItem(product_id=it.product_id, qty=it.qty,
                                           unit_cost_cents=it.unit_cost_cents))
        total += int(it.qty * it.unit_cost_cents)
        if product.cost_cents != it.unit_cost_cents:
            before = audit.snapshot(product)
            product.cost_cents = it.unit_cost_cents       # último custo
            audit.log(db, "product", product.id, "COST_CHANGE", before,
                      audit.snapshot(product), user)
    purchase.total_cents = total
    db.add(purchase)
    db.flush()
    for it in data.items:   # entrada de estoque na mesma transação
        stock_service.move(db, it.product_id, it.qty, "PURCHASE", "purchase", purchase.id)
    db.commit()
    return purchase
