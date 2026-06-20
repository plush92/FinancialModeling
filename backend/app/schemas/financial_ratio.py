from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.base import PeriodType


class FinancialRatioBase(BaseModel):
    company_id: int = Field(gt=0)
    fiscal_year: int = Field(ge=1900, le=2100)
    period_type: PeriodType
    currency: str = Field(default="USD", min_length=3, max_length=3)
    gross_margin: Decimal
    operating_margin: Decimal
    net_margin: Decimal
    current_ratio: Decimal
    quick_ratio: Decimal
    debt_to_equity: Decimal
    return_on_assets: Decimal
    return_on_equity: Decimal
    free_cash_flow_margin: Decimal
    interest_coverage: Decimal


class FinancialRatioCreate(FinancialRatioBase):
    pass


class FinancialRatioUpdate(BaseModel):
    company_id: int | None = Field(default=None, gt=0)
    fiscal_year: int | None = Field(default=None, ge=1900, le=2100)
    period_type: PeriodType | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    gross_margin: Decimal | None = None
    operating_margin: Decimal | None = None
    net_margin: Decimal | None = None
    current_ratio: Decimal | None = None
    quick_ratio: Decimal | None = None
    debt_to_equity: Decimal | None = None
    return_on_assets: Decimal | None = None
    return_on_equity: Decimal | None = None
    free_cash_flow_margin: Decimal | None = None
    interest_coverage: Decimal | None = None


class FinancialRatioRead(FinancialRatioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
