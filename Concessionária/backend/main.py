import os
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError

import models  # noqa: F401
from database import Base, engine
from routes import crm, people, sales, vehicles
from services.errors import BusinessError


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)   # em produção: Alembic
    yield


app = FastAPI(title="Concessionária API", lifespan=lifespan)


@app.middleware("http")
async def catch_all(request: Request, call_next):
    """Qualquer falha inesperada vira JSON 500 (e passa pelo CORS, que é adicionado depois)."""
    try:
        return await call_next(request)
    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"detail": f"Erro interno: {type(exc).__name__}: {exc}"})


app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
for r in (vehicles, people, crm, sales):
    app.include_router(r.router)


@app.exception_handler(BusinessError)
async def business_error(_: Request, exc: BusinessError):
    return JSONResponse(status_code=exc.status, content={"detail": exc.message})


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": [
        {"loc": [str(x) for x in e["loc"]], "msg": str(e["msg"])} for e in exc.errors()]})


@app.exception_handler(IntegrityError)
async def integrity_error(_: Request, exc: IntegrityError):
    return JSONResponse(status_code=409, content={"detail": "Registro duplicado (placa, chassi ou CPF/CNPJ já cadastrado)"})


FRONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
if os.path.isdir(FRONT):   # http://localhost:8000/ — montar por último
    app.mount("/", StaticFiles(directory=FRONT, html=True), name="front")
