from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from sqlalchemy.orm import Session
from database import now
from models import Lead, Sale, Seller, TestDrive, Vehicle


def build(db: Session, month: str | None) -> dict:
    first = date.fromisoformat((month or date.today().strftime("%Y-%m")) + "-01")
    nxt = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    start, end = datetime.combine(first, time.min), datetime.combine(nxt, time.min)

    stock = db.query(Vehicle).filter(Vehicle.status.notin_(["VENDIDO", "BAIXADO"])).all()
    by_status = Counter(v.status for v in stock)
    ages = [(now() - v.created_at).days for v in stock]

    sales = db.query(Sale).filter(Sale.status == "FECHADA", Sale.created_at >= start,
                                  Sale.created_at < end).all()
    rank: dict[int, dict] = defaultdict(lambda: {"sales": 0, "revenue_cents": 0, "commission_cents": 0})
    for s in sales:
        r = rank[s.seller_id]
        r["sales"] += 1
        r["revenue_cents"] += s.final_cents
        r["commission_cents"] += s.commission_cents
    names = {x.id: x.name for x in db.query(Seller)}
    ranking = sorted(({"seller": names.get(k, "?"), **v} for k, v in rank.items()),
                     key=lambda r: -r["revenue_cents"])

    leads = Counter(l.status for l in db.query(Lead))
    week = now() + timedelta(days=7)
    drives = db.query(TestDrive).filter(TestDrive.status == "AGENDADO",
                                        TestDrive.scheduled_at >= now(),
                                        TestDrive.scheduled_at <= week).count()
    return {
        "month": first.strftime("%Y-%m"),
        "stock": {"count": len(stock), "by_status": dict(by_status),
                  "value_cents": sum(v.price_cents for v in stock),
                  "cost_cents": sum(v.cost_cents for v in stock),
                  "avg_days": round(sum(ages) / len(ages)) if ages else 0,
                  "stale_over_90": sum(1 for a in ages if a > 90)},
        "sales": {"count": len(sales), "revenue_cents": sum(s.final_cents for s in sales),
                  "profit_cents": sum(s.profit_cents for s in sales),
                  "commission_cents": sum(s.commission_cents for s in sales),
                  "discount_cents": sum(s.discount_cents for s in sales)},
        "ranking": ranking, "leads": dict(leads), "test_drives_next_7_days": drives,
    }
