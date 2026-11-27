from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import now
from models import (CashSession, Customer, Payment, Product, Receivable,
                    ReceivablePayment, Sale, SaleItem)
from schemas.sale import Method, SaleIn
from . import audit_service as audit, stock_service
from .errors import BusinessError, NotFound
from .price_service import current_price


# ---------- Caixa ----------
def open_session(db: Session, opening_cents: int, user: str) -> CashSession:
    if db.query(CashSession).filter_by(user=user, closed_at=None).first():
        raise BusinessError("Este usuário já tem um caixa aberto", 409)
    s = CashSession(user=user, opening_cents=opening_cents)
    db.add(s)
    db.commit()
    return s


def _cash_in_session(db: Session, session_id: int) -> int:
    sales = db.query(Sale).filter_by(cash_session_id=session_id, status="COMPLETED").all()
    cash = sum(p.amount_cents for s in sales for p in s.payments if p.method == "CASH")
    cash -= sum(s.change_cents for s in sales)
    cash += (db.query(func.coalesce(func.sum(ReceivablePayment.amount_cents), 0))
             .filter_by(cash_session_id=session_id, method="CASH").scalar())
    return int(cash)


def close_session(db: Session, session_id: int, closing_cents: int) -> dict:
    s = db.get(CashSession, session_id)
    if not s:
        raise NotFound("Caixa")
    if s.closed_at:
        raise BusinessError("Caixa já fechado", 409)
    expected = s.opening_cents + _cash_in_session(db, session_id)
    s.closed_at, s.closing_cents = now(), closing_cents
    db.commit()
    return {"session_id": s.id, "expected_cents": expected,
            "closing_cents": closing_cents, "difference_cents": closing_cents - expected}


# ---------- Venda ----------
def create_sale(db: Session, data: SaleIn, user: str) -> Sale:
    existing = db.query(Sale).filter_by(idempotency_key=data.idempotency_key).first()
    if existing:                      # retry do PDV: devolve a mesma venda
        return existing

    session = db.get(CashSession, data.cash_session_id)
    if not session or session.closed_at:
        raise BusinessError("Caixa fechado ou inexistente", 409)

    sale = Sale(idempotency_key=data.idempotency_key, cash_session_id=session.id,
                customer_id=data.customer_id, discount_cents=data.discount_cents,
                created_by=user)
    subtotal = 0
    for it in data.items:
        product = db.get(Product, it.product_id)
        if not product or not product.active:
            raise BusinessError(f"Produto {it.product_id} inexistente ou inativo", 404)
        price = current_price(db, product.id)
        if price is None:
            raise BusinessError(f"Produto '{product.name}' sem preço", 409)
        line = int((Decimal(price) * it.qty).quantize(Decimal("1"), ROUND_HALF_UP))
        sale.items.append(SaleItem(product_id=product.id, qty=it.qty,
                                   unit_price_cents=price, total_cents=line))
        subtotal += line

    total = subtotal - data.discount_cents
    if total <= 0:
        raise BusinessError("Total da venda inválido")
    sale.total_cents = total

    # --- pagamentos ---
    cash = sum(p.amount_cents for p in data.payments if p.method == Method.CASH)
    others = sum(p.amount_cents for p in data.payments if p.method != Method.CASH)
    if others > total:
        raise BusinessError("Pagamentos não-dinheiro excedem o total")
    if cash + others < total:
        raise BusinessError("Pagamentos somam menos que o total")
    change = cash + others - total
    if change > cash:
        raise BusinessError("Troco maior que o valor pago em dinheiro")
    sale.change_cents = change
    for p in data.payments:
        sale.payments.append(Payment(method=p.method.value, amount_cents=p.amount_cents,
                                     details=p.details))
    db.add(sale)
    db.flush()

    # --- carnê ---
    for p in (p for p in data.payments if p.method == Method.INSTALLMENT):
        _create_receivables(db, sale, p.amount_cents, p.details, data.customer_id)

    # --- estoque ---
    for it in sale.items:
        stock_service.move(db, it.product_id, -it.qty, "SALE", "sale", sale.id)
    audit.log(db, "sale", sale.id, "CREATE", None, {"total_cents": total}, user)
    db.commit()
    return sale


def _create_receivables(db, sale, amount, details, customer_id):
    if not customer_id:
        raise BusinessError("Venda a prazo exige cliente cadastrado")
    customer = db.get(Customer, customer_id)
    if not customer:
        raise NotFound("Cliente")
    open_debt = (db.query(func.coalesce(func.sum(Receivable.amount_cents - Receivable.paid_cents), 0))
                 .filter_by(customer_id=customer_id, status="OPEN").scalar())
    if open_debt + amount > customer.credit_limit_cents:
        raise BusinessError("Limite de crédito do cliente excedido", 409)
    n = details["installments"]
    first = date.fromisoformat(details["first_due_date"])
    base, rest = divmod(amount, n)
    for i in range(n):
        month = first.month - 1 + i
        due = first.replace(year=first.year + month // 12, month=month % 12 + 1,
                            day=min(first.day, 28))
        db.add(Receivable(sale_id=sale.id, customer_id=customer_id, installment_no=i + 1,
                          due_date=due, amount_cents=base + (rest if i == 0 else 0)))


def cancel_sale(db: Session, sale_id: int, user: str) -> Sale:
    sale = db.get(Sale, sale_id)
    if not sale:
        raise NotFound("Venda")
    if sale.status == "CANCELED":
        raise BusinessError("Venda já cancelada", 409)
    recs = db.query(Receivable).filter_by(sale_id=sale_id).all()
    if any(r.paid_cents > 0 for r in recs):
        raise BusinessError("Há parcelas já pagas; faça estorno manual", 409)
    for r in recs:
        r.status = "CANCELED"
    for it in sale.items:    # estorno, nunca DELETE
        stock_service.move(db, it.product_id, it.qty, "SALE_CANCEL", "sale", sale.id)
    sale.status = "CANCELED"
    audit.log(db, "sale", sale.id, "CANCEL", {"status": "COMPLETED"}, {"status": "CANCELED"}, user)
    db.commit()
    return sale


# ---------- Contas a receber ----------
def pay_receivable(db: Session, rec_id: int, amount: int, method: str,
                   session_id: int | None) -> Receivable:
    rec = db.get(Receivable, rec_id)
    if not rec:
        raise NotFound("Parcela")
    if rec.status != "OPEN":
        raise BusinessError("Parcela não está em aberto", 409)
    if amount > rec.amount_cents - rec.paid_cents:
        raise BusinessError("Valor maior que o saldo da parcela")
    rec.paid_cents += amount
    if rec.paid_cents >= rec.amount_cents:
        rec.status = "PAID"
    db.add(ReceivablePayment(receivable_id=rec.id, amount_cents=amount,
                             method=method, cash_session_id=session_id))
    db.commit()
    return rec


# ---------- Relatório ----------
def daily_closing(db: Session, day: date) -> dict:
    start = datetime.combine(day, time.min)
    end = start + timedelta(days=1)
    totals: dict[str, int] = defaultdict(int)
    sales = db.query(Sale).filter(Sale.created_at >= start, Sale.created_at < end,
                                  Sale.status == "COMPLETED").all()
    for s in sales:
        for p in s.payments:
            totals[p.method] += p.amount_cents
        totals["CASH"] -= s.change_cents
    received: dict[str, int] = defaultdict(int)
    for rp in db.query(ReceivablePayment).filter(ReceivablePayment.created_at >= start,
                                                 ReceivablePayment.created_at < end):
        received[rp.method] += rp.amount_cents
    return {"date": str(day), "sales_count": len(sales),
            "sales_by_method_cents": dict(totals),
            "receivables_received_cents": dict(received)}
