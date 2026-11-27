import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError

import models  # noqa: F401  (registra as tabelas)
from database import Base, SessionLocal, engine
from routes import products, purchases, sales
from services.audit_service import purge_old
from services.errors import BusinessError


async def retention_loop():
    """Limpa o log de auditoria (> 7 dias) a cada 6h."""
    while True:
        with SessionLocal() as db:
            purge_old(db)
        await asyncio.sleep(6 * 3600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)   # em produção: usar Alembic
    task = asyncio.create_task(retention_loop())
    yield
    task.cancel()


app = FastAPI(title="Padaria API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(products.router)
app.include_router(purchases.router)
app.include_router(sales.router)


@app.exception_handler(BusinessError)
async def business_error(_: Request, exc: BusinessError):
    return JSONResponse(status_code=exc.status, content={"detail": exc.message})


@app.exception_handler(IntegrityError)
async def integrity_error(_: Request, exc: IntegrityError):
    return JSONResponse(status_code=409, content={"detail": "Registro duplicado ou inválido"})


# Front-end estático (pasta ../frontend) servido em http://localhost:8000/ — montar por último
FRONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
if os.path.isdir(FRONT):
    app.mount("/", StaticFiles(directory=FRONT, html=True), name="front")
