from decimal import Decimal

from app.models.base import PeriodType
from app.models.balance_sheet import BalanceSheet
from app.models.cash_flow_statement import CashFlowStatement
from app.models.company import Company
from app.models.income_statement import IncomeStatement
from app.services.ratio_engine_service import RatioEngineService


def _seed_period(db, company_id: int, fiscal_year: int, fiscal_period: str, *, revenue: str, gross_profit: str, operating_income: str, net_income: str, eps: str, cogs: str, ebitda: str, interest_expense: str, pretax_income: str, tax_expense: str, total_assets: str, total_equity: str, total_debt: str, total_current_assets: str, inventory: str, total_current_liabilities: str, cash: str, cash_and_equivalents: str, accounts_receivable: str, accounts_payable: str, cash_from_operations: str, capex: str) -> None:
    period_type = PeriodType.annual if fiscal_period == "FY" else PeriodType.quarterly

    income = IncomeStatement(
        company_id=company_id,
        fiscal_year=fiscal_year,
        fiscal_period=fiscal_period,
        period_type=period_type,
        currency="USD",
        revenue=Decimal(revenue),
        cogs=Decimal(cogs),
        gross_profit=Decimal(gross_profit),
        operating_expenses=Decimal("0"),
        ebitda=Decimal(ebitda),
        depreciation_and_amortization=Decimal("0"),
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
        fiscal_period=fiscal_period,
        period_type=period_type,
        currency="USD",
        cash=Decimal(cash),
        shareholder_equity=Decimal(total_equity),
        total_debt=Decimal(total_debt),
        cash_and_equivalents=Decimal(cash_and_equivalents),
        accounts_receivable=Decimal(accounts_receivable),
        inventory=Decimal(inventory),
        total_current_assets=Decimal(total_current_assets),
        property_plant_equipment=Decimal("0"),
        total_assets=Decimal(total_assets),
        accounts_payable=Decimal(accounts_payable),
        short_term_debt=Decimal("0"),
        total_current_liabilities=Decimal(total_current_liabilities),
        long_term_debt=Decimal(total_debt),
        total_liabilities=Decimal(total_assets) - Decimal(total_equity),
        total_equity=Decimal(total_equity),
    )

    cash_flow = CashFlowStatement(
        company_id=company_id,
        fiscal_year=fiscal_year,
        fiscal_period=fiscal_period,
        period_type=period_type,
        currency="USD",
        operating_cash_flow=Decimal(cash_from_operations),
        free_cash_flow=Decimal(cash_from_operations) - Decimal(capex),
        net_income=Decimal(net_income),
        depreciation_and_amortization=Decimal("0"),
        change_in_working_capital=Decimal("0"),
        cash_from_operations=Decimal(cash_from_operations),
        capex=Decimal(capex),
        cash_from_investing=Decimal("0"),
        debt_issued=Decimal("0"),
        debt_repaid=Decimal("0"),
        dividends_paid=Decimal("0"),
        cash_from_financing=Decimal("0"),
        net_change_in_cash=Decimal("0"),
        ending_cash=Decimal(cash),
    )

    db.add(income)
    db.add(balance)
    db.add(cash_flow)


def test_ratio_engine_calculates_profitability_and_growth(db_session):
    db = db_session
    company = Company(ticker="RAT", company_name="Ratio Co", name="Ratio Co", currency="USD", fiscal_year_end_month=12)
    db.add(company)
    db.commit()
    db.refresh(company)

    _seed_period(
        db,
        company.id,
        2024,
        "FY",
        revenue="1000",
        gross_profit="400",
        operating_income="150",
        net_income="100",
        eps="1.0",
        cogs="600",
        ebitda="200",
        interest_expense="10",
        pretax_income="130",
        tax_expense="30",
        total_assets="2000",
        total_equity="900",
        total_debt="700",
        total_current_assets="600",
        inventory="120",
        total_current_liabilities="300",
        cash="180",
        cash_and_equivalents="180",
        accounts_receivable="100",
        accounts_payable="90",
        cash_from_operations="180",
        capex="50",
    )
    _seed_period(
        db,
        company.id,
        2025,
        "FY",
        revenue="1200",
        gross_profit="540",
        operating_income="210",
        net_income="140",
        eps="1.4",
        cogs="660",
        ebitda="270",
        interest_expense="12",
        pretax_income="180",
        tax_expense="40",
        total_assets="2200",
        total_equity="1000",
        total_debt="720",
        total_current_assets="680",
        inventory="130",
        total_current_liabilities="320",
        cash="210",
        cash_and_equivalents="210",
        accounts_receivable="120",
        accounts_payable="95",
        cash_from_operations="230",
        capex="70",
    )
    db.commit()

    payload = RatioEngineService(db).get_ratios_payload("RAT")
    assert payload is not None

    profitability = payload["sections"]["profitability"]
    gross_margin = next(row for row in profitability if row["metric_name"] == "gross_margin")
    latest = Decimal(gross_margin["latest_value"])
    assert latest.quantize(Decimal("0.0001")) == Decimal("0.4500")

    growth_section = payload["sections"]["growth"]
    revenue_growth = next(row for row in growth_section if row["metric_name"] == "revenue_growth_yoy")
    growth_latest = Decimal(revenue_growth["latest_value"])
    assert growth_latest.quantize(Decimal("0.0001")) == Decimal("0.2000")


def test_ratio_engine_handles_divide_by_zero(db_session):
    db = db_session
    company = Company(ticker="ZERO", company_name="Zero Co", name="Zero Co", currency="USD", fiscal_year_end_month=12)
    db.add(company)
    db.commit()
    db.refresh(company)

    _seed_period(
        db,
        company.id,
        2025,
        "FY",
        revenue="0",
        gross_profit="0",
        operating_income="0",
        net_income="0",
        eps="0",
        cogs="0",
        ebitda="0",
        interest_expense="0",
        pretax_income="0",
        tax_expense="0",
        total_assets="1000",
        total_equity="500",
        total_debt="200",
        total_current_assets="100",
        inventory="50",
        total_current_liabilities="0",
        cash="20",
        cash_and_equivalents="20",
        accounts_receivable="10",
        accounts_payable="5",
        cash_from_operations="0",
        capex="0",
    )
    db.commit()

    trends_payload = RatioEngineService(db).get_trends_payload("ZERO")
    assert trends_payload is not None

    interest_coverage = next(item for item in trends_payload["trends"] if item["metric_name"] == "interest_coverage_ratio")
    assert interest_coverage["latest_value"] is None

    ratios_payload = RatioEngineService(db).get_ratios_payload("ZERO")
    liquidity = ratios_payload["sections"]["liquidity"]
    current_ratio = next(item for item in liquidity if item["metric_name"] == "current_ratio")
    assert current_ratio["latest_value"] is None


def test_trend_direction_and_rolling_average(db_session):
    db = db_session
    company = Company(ticker="TREND", company_name="Trend Co", name="Trend Co", currency="USD", fiscal_year_end_month=12)
    db.add(company)
    db.commit()
    db.refresh(company)

    for year, revenue in [(2021, "100"), (2022, "120"), (2023, "150"), (2024, "195")]:
        _seed_period(
            db,
            company.id,
            year,
            "FY",
            revenue=revenue,
            gross_profit=str(int(Decimal(revenue) * Decimal("0.4"))),
            operating_income=str(int(Decimal(revenue) * Decimal("0.15"))),
            net_income=str(int(Decimal(revenue) * Decimal("0.1"))),
            eps=str(Decimal(revenue) / Decimal("100")),
            cogs=str(int(Decimal(revenue) * Decimal("0.6"))),
            ebitda=str(int(Decimal(revenue) * Decimal("0.2"))),
            interest_expense="5",
            pretax_income="12",
            tax_expense="2",
            total_assets="500",
            total_equity="250",
            total_debt="100",
            total_current_assets="200",
            inventory="40",
            total_current_liabilities="100",
            cash="50",
            cash_and_equivalents="50",
            accounts_receivable="20",
            accounts_payable="15",
            cash_from_operations="30",
            capex="10",
        )
    db.commit()

    trends = RatioEngineService(db).get_trends_payload("TREND")
    assert trends is not None

    revenue_growth = next(item for item in trends["trends"] if item["metric_name"] == "revenue_growth_yoy")
    assert revenue_growth["trend_direction"] == "Improving"
    assert revenue_growth["rolling_average_3_periods"] is not None
