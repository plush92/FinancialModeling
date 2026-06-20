from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.base import PeriodType


class CashFlowStatementBase(BaseModel):
    company_id: int = Field(gt=0)
    fiscal_year: int = Field(ge=1900, le=2100)
    period_type: PeriodType
    currency: str = Field(default="USD", min_length=3, max_length=3)
    source_accession_number: str | None = Field(default=None, max_length=32)
    source_filing_date: date | None = None
    source_form: str | None = Field(default=None, max_length=12)
    net_income: Decimal
    depreciation_and_amortization: Decimal = Field(default=Decimal("0"))
    change_in_working_capital: Decimal = Field(default=Decimal("0"))
    cash_from_operations: Decimal
    capex: Decimal = Field(default=Decimal("0"))
    cash_from_investing: Decimal = Field(default=Decimal("0"))
    debt_issued: Decimal = Field(default=Decimal("0"))
    debt_repaid: Decimal = Field(default=Decimal("0"))
    dividends_paid: Decimal = Field(default=Decimal("0"))
    cash_from_financing: Decimal = Field(default=Decimal("0"))
    net_change_in_cash: Decimal
    ending_cash: Decimal


class CashFlowStatementCreate(CashFlowStatementBase):
    pass


class CashFlowStatementUpdate(BaseModel):
    company_id: int | None = Field(default=None, gt=0)
    fiscal_year: int | None = Field(default=None, ge=1900, le=2100)
    period_type: PeriodType | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    source_accession_number: str | None = Field(default=None, max_length=32)
    source_filing_date: date | None = None
    source_form: str | None = Field(default=None, max_length=12)
    net_income: Decimal | None = None
    depreciation_and_amortization: Decimal | None = None
    change_in_working_capital: Decimal | None = None
    cash_from_operations: Decimal | None = None
    capex: Decimal | None = None
    cash_from_investing: Decimal | None = None
    debt_issued: Decimal | None = None
    debt_repaid: Decimal | None = None
    dividends_paid: Decimal | None = None
    cash_from_financing: Decimal | None = None
    net_change_in_cash: Decimal | None = None
    ending_cash: Decimal | None = None


class CashFlowStatementRead(CashFlowStatementBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
