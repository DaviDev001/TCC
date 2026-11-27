from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator
from .vehicle import norm_plate

Method = Literal["PIX", "TED", "DINHEIRO", "CARTAO", "CHEQUE", "FINANCIAMENTO", "TROCA"]


class PaymentIn(BaseModel):
    method: Method
    amount_cents: int = Field(gt=0)
    # FINANCIAMENTO: {bank, installments}   TROCA: {brand, model, year, plate, [version, color, km, chassis]}
    details: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def check(self):
        d = self.details
        if self.method == "FINANCIAMENTO":
            if not d.get("bank") or not isinstance(d.get("installments"), int) or d["installments"] < 1:
                raise ValueError("Financiamento exige banco e nº de parcelas")
        if self.method == "TROCA":
            miss = [k for k in ("brand", "model", "year", "plate") if not d.get(k)]
            if miss:
                raise ValueError("Troca sem: " + ", ".join(miss))
            d["plate"] = norm_plate(d["plate"])
        return self


class SaleIn(BaseModel):
    vehicle_id: int
    customer_id: int
    seller_id: int
    lead_id: Optional[int] = None
    discount_cents: int = Field(0, ge=0)
    approved_by: Optional[str] = None
    payments: list[PaymentIn] = Field(min_length=1)
