from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.base import PeriodType


class IncomeStatementBase(BaseModel):
    company_id: int = Field(gt=0)
    fiscal_year: int = Field(ge=1900, le=2100)
    period_type: PeriodType
    currency: str = Field(default="USD", min_length=3, max_length=3)
    source_accession_number: str | None = Field(default=None, max_length=32)
    source_filing_date: date | None = None
    source_form: str | None = Field(default=None, max_length=12)
    revenue: Decimal = Field(ge=0)
    cogs: Decimal = Field(ge=0)
    gross_profit: Decimal
    operating_expenses: Decimal = Field(ge=0)
    ebitda: Decimal
    depreciation_and_amortization: Decimal = Field(default=Decimal("0"))
    operating_income: Decimal
    interest_expense: Decimal = Field(default=Decimal("0"))
    pretax_income: Decimal
    tax_expense: Decimal = Field(default=Decimal("0"))
    net_income: Decimal


class IncomeStatementCreate(IncomeStatementBase):
    pass


class IncomeStatementUpdate(BaseModel):
    company_id: int | None = Field(default=None, gt=0)
    fiscal_year: int | None = Field(default=None, ge=1900, le=2100)
    period_type: PeriodType | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    source_accession_number: str | None = Field(default=None, max_length=32)
    source_filing_date: date | None = None
    source_form: str | None = Field(default=None, max_length=12)
    revenue: Decimal | None = Field(default=None, ge=0)
    cogs: Decimal | None = Field(default=None, ge=0)
    gross_profit: Decimal | None = None
    operating_expenses: Decimal | None = Field(default=None, ge=0)
    ebitda: Decimal | None = None
    depreciation_and_amortization: Decimal | None = None
    operating_income: Decimal | None = None
    interest_expense: Decimal | None = None
    pretax_income: Decimal | None = None
    tax_expense: Decimal | None = None
    net_income: Decimal | None = None


class IncomeStatementRead(IncomeStatementBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
