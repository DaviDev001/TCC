"""Dados de exemplo:  python seed.py"""
from database import Base, SessionLocal, engine
import models
from models import Customer, Seller, Vehicle

Base.metadata.create_all(engine)
with SessionLocal() as db:
    if db.query(Vehicle).count():
        raise SystemExit("Banco já tem dados.")
    db.add_all([Seller(name="Carlos Lima", commission_pct=1.5), Seller(name="Ana Souza", commission_pct=2)])
    db.add_all([Customer(name="Maria Oliveira", document="12345678909", phone="(31) 99999-0001", city="Ipatinga"),
                Customer(name="João Pereira", document="98765432100", phone="(31) 98888-0002", city="Timóteo")])
    V = lambda *a, **k: Vehicle(**k)
    db.add_all([
        V(brand="Toyota", model="Corolla", version="XEi 2.0", year_fab=2021, year_model=2022, color="Prata", plate="ABC1D23", km=38000, fuel="FLEX", transmission="CVT", purchase_cents=9200000, price_cents=11490000),
        V(brand="Honda", model="Civic", version="EXL", year_fab=2020, year_model=2020, color="Preto", plate="DEF2G34", km=52000, fuel="FLEX", transmission="CVT", purchase_cents=8500000, price_cents=10290000),
        V(brand="Fiat", model="Argo", version="Drive 1.3", year_fab=2023, year_model=2024, color="Branco", plate="GHI3J45", km=9000, fuel="FLEX", transmission="MANUAL", purchase_cents=6400000, price_cents=7690000),
        V(brand="Chevrolet", model="Onix", version="LT", year_fab=2024, year_model=2025, color="Azul", km=0, condition="NOVO", purchase_cents=7000000, price_cents=8190000),
    ])
    db.commit()
print("Seed ok.")
