from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CompanyHistoricalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    company_name: str
    cik: int | None
    created_at: datetime
    updated_at: datetime


class IncomeStatementHistoricalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    fiscal_year: int
    fiscal_period: str
    revenue: Decimal
    gross_profit: Decimal
    operating_income: Decimal
    net_income: Decimal
    eps: Decimal


class BalanceSheetHistoricalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    fiscal_year: int
    fiscal_period: str
    cash: Decimal
    total_assets: Decimal
    total_liabilities: Decimal
    shareholder_equity: Decimal
    total_debt: Decimal


class CashFlowStatementHistoricalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    fiscal_year: int
    fiscal_period: str
    operating_cash_flow: Decimal
    capex: Decimal
    free_cash_flow: Decimal


class FinancialsBundleResponse(BaseModel):
    company: CompanyHistoricalRead
    income_statements: list[IncomeStatementHistoricalRead]
    balance_sheets: list[BalanceSheetHistoricalRead]
    cash_flow_statements: list[CashFlowStatementHistoricalRead]


class SyncResponse(BaseModel):
    ticker: str
    cik: int
    company_id: int
    synced_income_statements: int
    synced_balance_sheets: int
    synced_cash_flow_statements: int
    warnings_logged: int
