from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductIn(BaseModel):
    name: str = Field(min_length=1)
    barcode: Optional[str] = None
    unit: Literal["UN", "KG"] = "UN"
    cost_cents: int = Field(0, ge=0)


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    barcode: Optional[str] = None
    unit: Optional[Literal["UN", "KG"]] = None
    cost_cents: Optional[int] = Field(None, ge=0)
    active: Optional[bool] = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    barcode: Optional[str]
    unit: str
    cost_cents: int
    stock_balance: Decimal
    active: bool
    current_price_cents: Optional[int] = None


class PriceIn(BaseModel):
    price_cents: int = Field(gt=0)
    effective_from: Optional[datetime] = None  # None = vale a partir de agora


class PriceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    price_cents: int
    effective_from: datetime
    created_by: Optional[str]


class StockAdjustIn(BaseModel):
    product_id: int
    qty_delta: Decimal
    type: Literal["ADJUSTMENT", "LOSS"] = "ADJUSTMENT"
    reason: str = Field(min_length=3)
