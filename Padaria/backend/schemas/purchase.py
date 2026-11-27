from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SupplierIn(BaseModel):
    name: str = Field(min_length=1)
    document: Optional[str] = None
    phone: Optional[str] = None


class SupplierOut(SupplierIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PurchaseItemIn(BaseModel):
    product_id: int
    qty: Decimal = Field(gt=0)
    unit_cost_cents: int = Field(ge=0)


class PurchaseIn(BaseModel):
    supplier_id: int
    invoice_number: Optional[str] = None
    items: list[PurchaseItemIn] = Field(min_length=1)


class PurchaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    supplier_id: int
    invoice_number: Optional[str]
    total_cents: int
