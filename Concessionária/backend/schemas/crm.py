from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class LeadIn(BaseModel):
    name: str = Field(min_length=2)
    phone: Optional[str] = None
    email: Optional[str] = None
    source: Literal["LOJA", "SITE", "INDICACAO", "REDES", "TELEFONE"] = "LOJA"
    vehicle_id: Optional[int] = None
    seller_id: Optional[int] = None
    notes: Optional[str] = None


class LeadPatch(BaseModel):
    status: Optional[Literal["NOVO", "CONTATO", "VISITA", "PROPOSTA", "PERDIDO"]] = None
    notes: Optional[str] = None
    seller_id: Optional[int] = None
    lost_reason: Optional[str] = None


class TestDriveIn(BaseModel):
    vehicle_id: int
    customer_name: str = Field(min_length=2)
    phone: Optional[str] = None
    cnh: Optional[str] = None
    seller_id: Optional[int] = None
    lead_id: Optional[int] = None
    scheduled_at: datetime


class TestDrivePatch(BaseModel):
    status: Literal["REALIZADO", "CANCELADO"]
