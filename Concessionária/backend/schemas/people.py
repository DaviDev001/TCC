import re
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CustomerIn(BaseModel):
    name: str = Field(min_length=2)
    document: str
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None

    @field_validator("document")
    @classmethod
    def doc(cls, v):
        d = re.sub(r"\D", "", v)
        if len(d) not in (11, 14):
            raise ValueError("Informe CPF (11 dígitos) ou CNPJ (14 dígitos)")
        return d


class CustomerOut(CustomerIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class SellerIn(BaseModel):
    name: str = Field(min_length=2)
    commission_pct: Decimal = Field(Decimal("1.5"), ge=0, le=100)


class SellerOut(SellerIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    active: bool
