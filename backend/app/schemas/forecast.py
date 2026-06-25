from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ScenarioName = Literal["base", "bull", "bear"]


class ForecastRequest(BaseModel):
    scenario: ScenarioName = "base"
    assumptions_version: str = "latest"
    horizon_years: int | None = Field(default=None, ge=5, le=10)
    assumptions_override: dict[str, Any] | None = None


class ExplainabilityNode(BaseModel):
    formula: str
    inputs: dict[str, Any]
    source_historical_metric: str | None = None
    scenario_override: bool = False


class ForecastIncomeStatement(BaseModel):
    revenue: float
    cogs: float
    gross_profit: float
    operating_expenses: float
    operating_income: float
    interest_expense: float
    pretax_income: float
    tax_expense: float
    net_income: float
    eps: float


class ForecastBalanceSheet(BaseModel):
    cash: float
    accounts_receivable: float
    inventory: float
    accounts_payable: float
    total_assets: float
    total_liabilities: float
    shareholder_equity: float
    total_debt: float


class ForecastCashFlow(BaseModel):
    net_income: float
    depreciation_and_amortization: float
    change_in_working_capital: float
    operating_cash_flow: float
    capex: float
    investing_cash_flow: float
    debt_issued: float
    debt_repaid: float
    share_issuance: float
    share_buybacks: float
    financing_cash_flow: float
    free_cash_flow: float
    ending_cash_balance: float


class ForecastValidationReport(BaseModel):
    balance_sheet_balanced: bool
    cash_rollforward_reconciled: bool
    negative_asset_warnings: list[str]
    unreasonable_growth_flags: list[str]
    margin_sanity_flags: list[str]
    notes: list[str]


class ForecastPeriod(BaseModel):
    fiscal_year: int
    scenario: ScenarioName
    income_statement: ForecastIncomeStatement
    balance_sheet: ForecastBalanceSheet
    cash_flow_statement: ForecastCashFlow
    explainability: dict[str, ExplainabilityNode]


class ForecastResponse(BaseModel):
    ticker: str
    company_id: int
    scenario: ScenarioName
    assumptions_version: str
    generated_at: datetime
    assumptions: dict[str, Any]
    validation: ForecastValidationReport
    projections: list[ForecastPeriod]


class ForecastScenariosResponse(BaseModel):
    ticker: str
    company_id: int
    assumptions_version: str
    generated_at: datetime
    scenarios: dict[str, ForecastResponse]
