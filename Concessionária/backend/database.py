import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./concessionaria.db")
_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


def now() -> datetime:
    return datetime.now()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
