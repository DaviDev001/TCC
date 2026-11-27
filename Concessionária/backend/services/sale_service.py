import os
from decimal import ROUND_HALF_UP, Decimal
from sqlalchemy.orm import Session
from database import now
from models import Customer, Lead, Sale, SalePayment, Seller, Vehicle
from schemas.sale import SaleIn
from . import audit_service as audit
from .errors import BusinessError, NotFound

# Desconto acima deste % do preço exige "approved_by" (gerente)
MAX_DISCOUNT_PCT = Decimal(os.getenv("MAX_DISCOUNT_PCT", "5"))


def create_sale(db: Session, data: SaleIn, user: str) -> Sale:
    v = db.query(Vehicle).filter(Vehicle.id == data.vehicle_id).with_for_update().first()
    if not v:
        raise NotFound("Veículo")
    if v.status not in ("DISPONIVEL", "RESERVADO"):
        raise BusinessError(f"Veículo não está disponível para venda (status {v.status})", 409)
    if not db.get(Customer, data.customer_id):
        raise NotFound("Cliente")
    seller = db.get(Seller, data.seller_id)
    if not seller or not seller.active:
        raise NotFound("Vendedor")
    if v.price_cents <= 0:
        raise BusinessError("Veículo sem preço de venda definido", 409)

    if data.discount_cents > Decimal(v.price_cents) * MAX_DISCOUNT_PCT / 100 and not data.approved_by:
        raise BusinessError(f"Desconto acima de {MAX_DISCOUNT_PCT}% exige aprovação do gerente", 403)
    final = v.price_cents - data.discount_cents
    if final <= 0:
        raise BusinessError("Valor final inválido")
    paid = sum(p.amount_cents for p in data.payments)
    if paid != final:
        raise BusinessError(f"Pagamentos somam {paid / 100:.2f}, mas o valor final é {final / 100:.2f}")

    cost = v.cost_cents
    profit = final - cost
    commission = int((Decimal(max(profit, 0)) * Decimal(seller.commission_pct) / 100)
                     .quantize(Decimal("1"), ROUND_HALF_UP))
    sale = Sale(vehicle_id=v.id, customer_id=data.customer_id, seller_id=seller.id,
                lead_id=data.lead_id, list_price_cents=v.price_cents,
                discount_cents=data.discount_cents, final_cents=final, cost_cents=cost,
                profit_cents=profit, commission_cents=commission,
                approved_by=data.approved_by, created_by=user)
    db.add(sale)
    db.flush()

    for p in data.payments:
        det = dict(p.details)
        if p.method == "TROCA":      # o carro recebido entra no estoque, em preparação
            tv = Vehicle(brand=det["brand"], model=det["model"], version=det.get("version"),
                         year_fab=int(det["year"]), year_model=int(det["year"]),
                         color=det.get("color") or "—", plate=det["plate"],
                         chassis=(det.get("chassis") or None), km=int(det.get("km") or 0),
                         condition="USADO", purchase_cents=p.amount_cents,
                         price_cents=p.amount_cents, status="MANUTENCAO",
                         notes=f"Recebido na troca (venda {sale.id})")
            db.add(tv)
            db.flush()
            det["vehicle_id"] = tv.id
            audit.log(db, "vehicle", tv.id, "CREATE_TRADE_IN", None, audit.snapshot(tv), user)
        sale.payments.append(SalePayment(method=p.method, amount_cents=p.amount_cents, details=det))

    v.status, v.sold_at = "VENDIDO", now()
    if data.lead_id:
        lead = db.get(Lead, data.lead_id)
        if lead:
            lead.status = "GANHO"
    audit.log(db, "sale", sale.id, "CREATE", None,
              {"vehicle": v.desc, "final_cents": final, "profit_cents": profit}, user)
    db.commit()
    return sale


def cancel_sale(db: Session, sale_id: int, user: str) -> Sale:
    sale = db.get(Sale, sale_id)
    if not sale:
        raise NotFound("Venda")
    if sale.status == "CANCELADA":
        raise BusinessError("Venda já cancelada", 409)
    for p in sale.payments:                      # veículo de troca: sai do estoque
        if p.method == "TROCA" and p.details.get("vehicle_id"):
            tv = db.get(Vehicle, p.details["vehicle_id"])
            if tv and tv.status == "VENDIDO":
                raise BusinessError("O veículo recebido na troca já foi vendido; não é possível cancelar", 409)
            if tv:
                tv.status = "BAIXADO"
    v = db.get(Vehicle, sale.vehicle_id)
    v.status, v.sold_at = "DISPONIVEL", None
    sale.status = "CANCELADA"
    audit.log(db, "sale", sale.id, "CANCEL", {"status": "FECHADA"}, {"status": "CANCELADA"}, user)
    db.commit()
    return sale
