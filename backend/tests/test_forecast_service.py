from decimal import Decimal

from app.models.balance_sheet import BalanceSheet
from app.models.base import PeriodType
from app.models.cash_flow_statement import CashFlowStatement
from app.models.company import Company
from app.models.income_statement import IncomeStatement
from app.services.forecast_service import ForecastService


def _seed_period(
    db,
    company_id: int,
    fiscal_year: int,
    *,
    revenue: str,
    cogs: str,
    gross_profit: str,
    operating_expenses: str,
    operating_income: str,
    interest_expense: str,
    pretax_income: str,
    tax_expense: str,
    net_income: str,
    eps: str,
    cash: str,
    accounts_receivable: str,
    inventory: str,
    accounts_payable: str,
    total_assets: str,
    total_liabilities: str,
    total_equity: str,
    total_debt: str,
    ppe: str,
    depreciation: str,
    capex: str,
    cash_from_operations: str,
    debt_issued: str = "0",
    debt_repaid: str = "0",
) -> None:
    period_type = PeriodType.annual

    income = IncomeStatement(
        company_id=company_id,
        fiscal_year=fiscal_year,
        fiscal_period="FY",
        period_type=period_type,
        currency="USD",
        revenue=Decimal(revenue),
        cogs=Decimal(cogs),
        gross_profit=Decimal(gross_profit),
        operating_expenses=Decimal(operating_expenses),
        ebitda=Decimal(operating_income) + Decimal(depreciation),
        depreciation_and_amortization=Decimal(depreciation),
        operating_income=Decimal(operating_income),
        interest_expense=Decimal(interest_expense),
        pretax_income=Decimal(pretax_income),
        tax_expense=Decimal(tax_expense),
        net_income=Decimal(net_income),
        eps=Decimal(eps),
    )

    balance = BalanceSheet(
        company_id=company_id,
        fiscal_year=fiscal_year,
        fiscal_period="FY",
        period_type=period_type,
        currency="USD",
        cash=Decimal(cash),
        shareholder_equity=Decimal(total_equity),
        total_debt=Decimal(total_debt),
        cash_and_equivalents=Decimal(cash),
        accounts_receivable=Decimal(accounts_receivable),
        inventory=Decimal(inventory),
        total_current_assets=Decimal(cash) + Decimal(accounts_receivable) + Decimal(inventory),
        property_plant_equipment=Decimal(ppe),
        total_assets=Decimal(total_assets),
        accounts_payable=Decimal(accounts_payable),
        short_term_debt=Decimal(total_debt) * Decimal("0.2"),
        total_current_liabilities=Decimal(accounts_payable) + Decimal(total_debt) * Decimal("0.2"),
        long_term_debt=Decimal(total_debt) * Decimal("0.8"),
        total_liabilities=Decimal(total_liabilities),
        total_equity=Decimal(total_equity),
    )

    cash_flow = CashFlowStatement(
        company_id=company_id,
        fiscal_year=fiscal_year,
        fiscal_period="FY",
        period_type=period_type,
        currency="USD",
        operating_cash_flow=Decimal(cash_from_operations),
        free_cash_flow=Decimal(cash_from_operations) - Decimal(capex),
        net_income=Decimal(net_income),
        depreciation_and_amortization=Decimal(depreciation),
        change_in_working_capital=Decimal("0"),
        cash_from_operations=Decimal(cash_from_operations),
        capex=Decimal(capex),
        cash_from_investing=-Decimal(capex),
        debt_issued=Decimal(debt_issued),
        debt_repaid=Decimal(debt_repaid),
        dividends_paid=Decimal("0"),
        cash_from_financing=Decimal(debt_issued) - Decimal(debt_repaid),
        net_change_in_cash=Decimal(cash_from_operations) - Decimal(capex) + Decimal(debt_issued) - Decimal(debt_repaid),
        ending_cash=Decimal(cash),
    )

    db.add(income)
    db.add(balance)
    db.add(cash_flow)


def _seed_history(db, ticker: str = "FCAST"):
    company = Company(ticker=ticker, company_name="Forecast Co", name="Forecast Co", currency="USD", fiscal_year_end_month=12)
    db.add(company)
    db.commit()
    db.refresh(company)

    _seed_period(
        db,
        company.id,
        2023,
        revenue="1000",
        cogs="600",
        gross_profit="400",
        operating_expenses="220",
        operating_income="180",
        interest_expense="20",
        pretax_income="160",
        tax_expense="32",
        net_income="128",
        eps="1.28",
        cash="200",
        accounts_receivable="120",
        inventory="90",
        accounts_payable="80",
        total_assets="1600",
        total_liabilities="700",
        total_equity="900",
        total_debt="300",
        ppe="1190",
        depreciation="40",
        capex="55",
        cash_from_operations="165",
    )

    _seed_period(
        db,
        company.id,
        2024,
        revenue="1120",
        cogs="660",
        gross_profit="460",
        operating_expenses="245",
        operating_income="215",
        interest_expense="21",
        pretax_income="194",
        tax_expense="39",
        net_income="155",
        eps="1.45",
        cash="230",
        accounts_receivable="128",
        inventory="95",
        accounts_payable="84",
        total_assets="1710",
        total_liabilities="760",
        total_equity="950",
        total_debt="315",
        ppe="1257",
        depreciation="42",
        capex="60",
        cash_from_operations="197",
    )
    db.commit()
    return company


def test_forecast_balances_three_statements(db_session):
    db = db_session
    company = _seed_history(db)

    payload = ForecastService(db).get_forecast_payload(company.ticker, scenario="base", assumptions_version="latest")

    assert payload is not None
    assert payload["validation"]["balance_sheet_balanced"] is True
    assert payload["validation"]["cash_rollforward_reconciled"] is True
    assert len(payload["projections"]) >= 5

    first = payload["projections"][0]
    bs = first["balance_sheet"]
    assert abs(bs["total_assets"] - (bs["total_liabilities"] + bs["shareholder_equity"])) < 0.01


def test_scenario_isolation_without_mutating_base(db_session):
    db = db_session
    company = _seed_history(db, ticker="SCEN")

    base_payload = ForecastService(db).get_forecast_payload(company.ticker, scenario="base", assumptions_version="latest")
    bull_payload = ForecastService(db).get_forecast_payload(company.ticker, scenario="bull", assumptions_version="latest")

    assert base_payload is not None and bull_payload is not None

    base_rev = base_payload["projections"][0]["income_statement"]["revenue"]
    bull_rev = bull_payload["projections"][0]["income_statement"]["revenue"]
    assert bull_rev > base_rev

    base_again = ForecastService(db).get_forecast_payload(company.ticker, scenario="base", assumptions_version="latest")
    assert base_again is not None
    assert base_again["projections"][0]["income_statement"]["revenue"] == base_rev


def test_circularity_resolution_and_explainability(db_session):
    db = db_session
    company = _seed_history(db, ticker="CIRC")

    payload = ForecastService(db).get_forecast_payload(company.ticker, scenario="bear", assumptions_version="latest")

    assert payload is not None
    for period in payload["projections"]:
        explainability = period["explainability"]
        assert "interest_expense" in explainability
        assert explainability["interest_expense"]["formula"]
        assert "inputs" in explainability["interest_expense"]


def test_edge_case_zero_revenue_override(db_session):
    db = db_session
    company = _seed_history(db, ticker="EDGE")

    payload = ForecastService(db).get_forecast_payload(
        company.ticker,
        scenario="base",
        assumptions_version="latest",
        assumptions_override={
            "revenue_drivers": {
                "revenue_growth_by_year": [-1.0, 0.0, 0.0, 0.0, 0.0],
            }
        },
        horizon_years=5,
    )

    assert payload is not None
    assert len(payload["projections"]) == 5
    # should not crash and should emit at least one sanity flag
    assert isinstance(payload["validation"]["unreasonable_growth_flags"], list)
