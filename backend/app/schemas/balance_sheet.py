from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.base import PeriodType


class BalanceSheetBase(BaseModel):
    company_id: int = Field(gt=0)
    fiscal_year: int = Field(ge=1900, le=2100)
    period_type: PeriodType
    currency: str = Field(default="USD", min_length=3, max_length=3)
    cash_and_equivalents: Decimal = Field(ge=0)
    accounts_receivable: Decimal = Field(ge=0)
    inventory: Decimal = Field(ge=0)
    total_current_assets: Decimal = Field(ge=0)
    property_plant_equipment: Decimal = Field(ge=0)
    total_assets: Decimal = Field(ge=0)
    accounts_payable: Decimal = Field(ge=0)
    short_term_debt: Decimal = Field(ge=0)
    total_current_liabilities: Decimal = Field(ge=0)
    long_term_debt: Decimal = Field(ge=0)
    total_liabilities: Decimal = Field(ge=0)
    total_equity: Decimal = Field(ge=0)


class BalanceSheetCreate(BalanceSheetBase):
    pass


class BalanceSheetUpdate(BaseModel):
    company_id: int | None = Field(default=None, gt=0)
    fiscal_year: int | None = Field(default=None, ge=1900, le=2100)
    period_type: PeriodType | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    cash_and_equivalents: Decimal | None = None
    accounts_receivable: Decimal | None = None
    inventory: Decimal | None = None
    total_current_assets: Decimal | None = None
    property_plant_equipment: Decimal | None = None
    total_assets: Decimal | None = None
    accounts_payable: Decimal | None = None
    short_term_debt: Decimal | None = None
    total_current_liabilities: Decimal | None = None
    long_term_debt: Decimal | None = None
    total_liabilities: Decimal | None = None
    total_equity: Decimal | None = None


class BalanceSheetRead(BalanceSheetBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
