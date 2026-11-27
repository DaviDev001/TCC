import os
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLite para desenvolvimento. Em produção: postgresql+psycopg://user:pass@host/padaria
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./padaria.db")
_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


def now() -> datetime:
    """Horário local (naive) da padaria. Usado em todo o sistema."""
    return datetime.now()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
