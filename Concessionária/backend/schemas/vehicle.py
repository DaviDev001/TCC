import re
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Fuel = Literal["FLEX", "GASOLINA", "ETANOL", "DIESEL", "HIBRIDO", "ELETRICO", "GNV"]
Trans = Literal["MANUAL", "AUTOMATICO", "CVT", "AUTOMATIZADO"]
PLATE_RE = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")   # antiga (ABC1234) e Mercosul (ABC1D23)


def norm_plate(v: Optional[str]) -> Optional[str]:
    if not v:
        return None
    v = re.sub(r"[^A-Za-z0-9]", "", v).upper()
    if not PLATE_RE.match(v):
        raise ValueError("Placa inválida (ex.: ABC1D23 ou ABC1234)")
    return v


class VehicleIn(BaseModel):
    brand: str = Field(min_length=1)
    model: str = Field(min_length=1)
    version: Optional[str] = None
    year_fab: int = Field(ge=1950, le=2100)
    year_model: int = Field(ge=1950, le=2100)
    color: str = Field(min_length=1)
    plate: Optional[str] = None
    chassis: Optional[str] = None
    km: int = Field(0, ge=0)
    fuel: Fuel = "FLEX"
    transmission: Trans = "MANUAL"
    condition: Literal["NOVO", "USADO"] = "USADO"
    purchase_cents: int = Field(0, ge=0)
    price_cents: int = Field(0, ge=0)
    notes: Optional[str] = None

    @field_validator("plate")
    @classmethod
    def plate_ok(cls, v):
        return norm_plate(v)

    @field_validator("chassis")
    @classmethod
    def chassis_ok(cls, v):
        if not v:
            return None
        v = v.strip().upper()
        if not re.match(r"^[A-HJ-NPR-Z0-9]{17}$", v):
            raise ValueError("Chassi deve ter 17 caracteres (sem I, O, Q)")
        return v

    @model_validator(mode="after")
    def years(self):
        if self.year_model < self.year_fab:
            raise ValueError("Ano do modelo não pode ser menor que o de fabricação")
        return self


class VehicleUpdate(BaseModel):
    version: Optional[str] = None
    color: Optional[str] = None
    km: Optional[int] = Field(None, ge=0)
    fuel: Optional[Fuel] = None
    transmission: Optional[Trans] = None
    purchase_cents: Optional[int] = Field(None, ge=0)
    price_cents: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None


class StatusIn(BaseModel):
    status: Literal["DISPONIVEL", "RESERVADO", "MANUTENCAO", "BAIXADO"]


class ExpenseIn(BaseModel):
    description: str = Field(min_length=2)
    amount_cents: int = Field(gt=0)


class ExpenseOut(ExpenseIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class VehicleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    desc: str
    brand: str
    model: str
    version: Optional[str]
    year_fab: int
    year_model: int
    color: str
    plate: Optional[str]
    chassis: Optional[str]
    km: int
    fuel: str
    transmission: str
    condition: str
    purchase_cents: int
    expenses_cents: int
    cost_cents: int
    price_cents: int
    status: str
    notes: Optional[str]
    created_at: datetime
    expenses: list[ExpenseOut] = []
