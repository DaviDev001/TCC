from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Method(str, Enum):
    PIX = "PIX"
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"
    CASH = "CASH"
    CHECK = "CHECK"
    INSTALLMENT = "INSTALLMENT"  # carnê / a prazo


class PaymentIn(BaseModel):
    method: Method
    amount_cents: int = Field(gt=0)
    # PIX/cartão: {"nsu": "...", "brand": "visa"}
    # CHECK: {"bank","number","holder","due_date"}
    # INSTALLMENT: {"installments": 3, "first_due_date": "2026-12-24"}
    details: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_details(self):
        d = self.details
        if self.method == Method.CHECK:
            missing = [k for k in ("bank", "number", "holder", "due_date") if not d.get(k)]
            if missing:
                raise ValueError(f"Cheque sem: {', '.join(missing)}")
        if self.method == Method.INSTALLMENT:
            n = d.get("installments")
            if not isinstance(n, int) or n < 1 or n > 24:
                raise ValueError("installments deve ser inteiro entre 1 e 24")
            date.fromisoformat(d.get("first_due_date", ""))  # lança erro se inválida
        return self


class SaleItemIn(BaseModel):
    product_id: int
    qty: Decimal = Field(gt=0)


class SaleIn(BaseModel):
    idempotency_key: str = Field(min_length=8)
    cash_session_id: int
    customer_id: Optional[int] = None
    discount_cents: int = Field(0, ge=0)
    items: list[SaleItemIn] = Field(min_length=1)
    payments: list[PaymentIn] = Field(min_length=1)


class SaleItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_id: int
    qty: Decimal
    unit_price_cents: int
    total_cents: int


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    method: str
    amount_cents: int
    details: dict


class SaleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    total_cents: int
    discount_cents: int
    change_cents: int
    created_at: datetime
    items: list[SaleItemOut]
    payments: list[PaymentOut]


class CashOpenIn(BaseModel):
    opening_cents: int = Field(0, ge=0)


class CashCloseIn(BaseModel):
    closing_cents: int = Field(ge=0)


class ReceivablePayIn(BaseModel):
    amount_cents: int = Field(gt=0)
    method: Method
    cash_session_id: Optional[int] = None
