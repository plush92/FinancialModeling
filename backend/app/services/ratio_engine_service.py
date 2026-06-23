from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from math import isfinite
from typing import Any

from sqlalchemy.orm import Session

from app.models.balance_sheet import BalanceSheet
from app.models.base import PeriodType
from app.models.cash_flow_statement import CashFlowStatement
from app.models.company import Company
from app.models.financial_metric import FinancialMetric
from app.models.income_statement import IncomeStatement


CALCULATION_VERSION = "2.0.0"

PERIOD_ORDER = {
    "Q1": 1,
    "Q2": 2,
    "Q3": 3,
    "Q4": 4,
    "FY": 5,
}


@dataclass(frozen=True)
class MetricDefinition:
    display_name: str
    category: str
    unit: str
    formula: str
    source_metrics: list[str]
    directionality: str


METRIC_DEFINITIONS: dict[str, MetricDefinition] = {
    "gross_margin": MetricDefinition("Gross Margin", "profitability", "percent", "gross_profit / revenue", ["gross_profit", "revenue"], "higher"),
    "operating_margin": MetricDefinition("Operating Margin", "profitability", "percent", "operating_income / revenue", ["operating_income", "revenue"], "higher"),
    "net_margin": MetricDefinition("Net Margin", "profitability", "percent", "net_income / revenue", ["net_income", "revenue"], "higher"),
    "ebitda_margin": MetricDefinition("EBITDA Margin", "profitability", "percent", "ebitda / revenue", ["ebitda", "revenue"], "higher"),
    "roa": MetricDefinition("Return on Assets (ROA)", "profitability", "percent", "net_income / average_total_assets", ["net_income", "total_assets"], "higher"),
    "roe": MetricDefinition("Return on Equity (ROE)", "profitability", "percent", "net_income / average_total_equity", ["net_income", "total_equity"], "higher"),
    "roic": MetricDefinition("Return on Invested Capital (ROIC)", "profitability", "percent", "nopat / (total_debt + total_equity - cash_and_equivalents)", ["operating_income", "tax_expense", "pretax_income", "total_debt", "total_equity", "cash_and_equivalents"], "higher"),
    "current_ratio": MetricDefinition("Current Ratio", "liquidity", "multiple", "total_current_assets / total_current_liabilities", ["total_current_assets", "total_current_liabilities"], "higher"),
    "quick_ratio": MetricDefinition("Quick Ratio", "liquidity", "multiple", "(total_current_assets - inventory) / total_current_liabilities", ["total_current_assets", "inventory", "total_current_liabilities"], "higher"),
    "cash_ratio": MetricDefinition("Cash Ratio", "liquidity", "multiple", "cash / total_current_liabilities", ["cash", "total_current_liabilities"], "higher"),
    "debt_to_equity": MetricDefinition("Debt-to-Equity", "leverage", "multiple", "total_debt / total_equity", ["total_debt", "total_equity"], "lower"),
    "debt_to_assets": MetricDefinition("Debt-to-Assets", "leverage", "multiple", "total_debt / total_assets", ["total_debt", "total_assets"], "lower"),
    "interest_coverage_ratio": MetricDefinition("Interest Coverage Ratio", "leverage", "multiple", "operating_income / abs(interest_expense)", ["operating_income", "interest_expense"], "higher"),
    "net_debt_to_ebitda": MetricDefinition("Net Debt / EBITDA", "leverage", "multiple", "(total_debt - cash_and_equivalents) / ebitda", ["total_debt", "cash_and_equivalents", "ebitda"], "lower"),
    "asset_turnover": MetricDefinition("Asset Turnover", "efficiency", "multiple", "revenue / average_total_assets", ["revenue", "total_assets"], "higher"),
    "inventory_turnover": MetricDefinition("Inventory Turnover", "efficiency", "multiple", "cogs / average_inventory", ["cogs", "inventory"], "higher"),
    "receivables_turnover": MetricDefinition("Receivables Turnover", "efficiency", "multiple", "revenue / average_accounts_receivable", ["revenue", "accounts_receivable"], "higher"),
    "dso": MetricDefinition("Days Sales Outstanding (DSO)", "efficiency", "days", "365 / receivables_turnover", ["revenue", "accounts_receivable"], "lower"),
    "dio": MetricDefinition("Days Inventory Outstanding (DIO)", "efficiency", "days", "365 / inventory_turnover", ["cogs", "inventory"], "lower"),
    "ccc": MetricDefinition("Cash Conversion Cycle (CCC)", "efficiency", "days", "dso + dio - dpo", ["accounts_receivable", "inventory", "accounts_payable", "revenue", "cogs"], "lower"),
    "free_cash_flow": MetricDefinition("Free Cash Flow", "cash_flow", "currency", "cash_from_operations - capex", ["cash_from_operations", "capex"], "higher"),
    "free_cash_flow_margin": MetricDefinition("Free Cash Flow Margin", "cash_flow", "percent", "free_cash_flow / revenue", ["free_cash_flow", "revenue"], "higher"),
    "cash_conversion_ratio": MetricDefinition("Cash Conversion Ratio", "cash_flow", "multiple", "cash_from_operations / net_income", ["cash_from_operations", "net_income"], "higher"),
    "capex_as_pct_revenue": MetricDefinition("CapEx as % of Revenue", "cash_flow", "percent", "capex / revenue", ["capex", "revenue"], "lower"),
    "revenue_growth_yoy": MetricDefinition("Revenue Growth YoY", "growth", "percent", "(revenue - prior_year_revenue) / abs(prior_year_revenue)", ["revenue", "prior_year_revenue"], "higher"),
    "gross_profit_growth_yoy": MetricDefinition("Gross Profit Growth YoY", "growth", "percent", "(gross_profit - prior_year_gross_profit) / abs(prior_year_gross_profit)", ["gross_profit", "prior_year_gross_profit"], "higher"),
    "operating_income_growth_yoy": MetricDefinition("Operating Income Growth YoY", "growth", "percent", "(operating_income - prior_year_operating_income) / abs(prior_year_operating_income)", ["operating_income", "prior_year_operating_income"], "higher"),
    "net_income_growth_yoy": MetricDefinition("Net Income Growth YoY", "growth", "percent", "(net_income - prior_year_net_income) / abs(prior_year_net_income)", ["net_income", "prior_year_net_income"], "higher"),
    "eps_growth_yoy": MetricDefinition("EPS Growth YoY", "growth", "percent", "(eps - prior_year_eps) / abs(prior_year_eps)", ["eps", "prior_year_eps"], "higher"),
    "free_cash_flow_growth_yoy": MetricDefinition("Free Cash Flow Growth YoY", "growth", "percent", "(free_cash_flow - prior_year_free_cash_flow) / abs(prior_year_free_cash_flow)", ["free_cash_flow", "prior_year_free_cash_flow"], "higher"),
}

SECTION_ORDER = ["profitability", "liquidity", "leverage", "efficiency", "cash_flow", "growth"]


def ratio_direction(metric_name: str) -> str:
    definition = METRIC_DEFINITIONS.get(metric_name)
    if definition is None:
        return "higher"
    return definition.directionality


class RatioEngineService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_ratios_payload(self, ticker: str) -> dict[str, Any] | None:
        company = self._get_company(ticker)
        if company is None:
            return None

        metric_rows = self._refresh_metrics(company)
        grouped = self._group_metric_rows(metric_rows)
        trends = self._compute_trends(grouped)

        sections: dict[str, list[dict[str, Any]]] = {section: [] for section in SECTION_ORDER}
        for metric_name, series in grouped.items():
            definition = METRIC_DEFINITIONS.get(metric_name)
            if definition is None:
                continue
            point_history = [
                {
                    "fiscal_year": item["fiscal_year"],
                    "fiscal_period": item["fiscal_period"],
                    "value": item["metric_value"],
                }
                for item in series
            ]
            latest_inputs_used = {}
            latest_row = next(
                (
                    row
                    for row in reversed(metric_rows)
                    if row.metric_name == metric_name
                ),
                None,
            )
            if latest_row is not None:
                latest_inputs_used = latest_row.inputs_used
            sections[definition.category].append(
                {
                    "metric_name": metric_name,
                    "display_name": definition.display_name,
                    "category": definition.category,
                    "unit": definition.unit,
                    "formula": definition.formula,
                    "source_metrics": definition.source_metrics,
                    "latest_inputs_used": latest_inputs_used,
                    "history": point_history,
                    "latest_value": point_history[-1]["value"] if point_history else None,
                    "trend_direction": trends.get(metric_name, {}).get("trend_direction"),
                }
            )

        for section in sections:
            sections[section].sort(key=lambda item: item["display_name"])

        kpi_metric_names = [
            "gross_margin",
            "net_margin",
            "current_ratio",
            "debt_to_equity",
            "free_cash_flow",
            "revenue_growth_yoy",
        ]
        kpi_summary = []
        for metric_name in kpi_metric_names:
            definition = METRIC_DEFINITIONS[metric_name]
            history = grouped.get(metric_name, [])
            latest_value = history[-1]["metric_value"] if history else None
            kpi_summary.append(
                {
                    "metric_name": metric_name,
                    "display_name": definition.display_name,
                    "category": definition.category,
                    "unit": definition.unit,
                    "value": latest_value,
                    "trend_direction": trends.get(metric_name, {}).get("trend_direction"),
                }
            )

        historical_periods = self._build_historical_periods(metric_rows)

        return {
            "ticker": company.ticker,
            "company_id": company.id,
            "calculation_version": CALCULATION_VERSION,
            "generated_at": datetime.now(timezone.utc),
            "historical_periods": historical_periods,
            "sections": sections,
            "kpi_summary": kpi_summary,
        }

    def get_metrics_payload(self, ticker: str) -> dict[str, Any] | None:
        company = self._get_company(ticker)
        if company is None:
            return None

        metric_rows = self._refresh_metrics(company)
        return {
            "ticker": company.ticker,
            "company_id": company.id,
            "calculation_version": CALCULATION_VERSION,
            "metrics": metric_rows,
        }

    def get_trends_payload(self, ticker: str) -> dict[str, Any] | None:
        company = self._get_company(ticker)
        if company is None:
            return None

        metric_rows = self._refresh_metrics(company)
        grouped = self._group_metric_rows(metric_rows)
        trends = self._compute_trends(grouped)

        ordered_trends: list[dict[str, Any]] = []
        for metric_name, trend in trends.items():
            definition = METRIC_DEFINITIONS.get(metric_name)
            if definition is None:
                continue
            ordered_trends.append(
                {
                    "metric_name": metric_name,
                    "display_name": definition.display_name,
                    "category": definition.category,
                    "latest_value": trend["latest_value"],
                    "previous_value": trend["previous_value"],
                    "cagr_3y": trend["cagr_3y"],
                    "cagr_5y": trend["cagr_5y"],
                    "rolling_average_3_periods": trend["rolling_average_3_periods"],
                    "trend_direction": trend["trend_direction"],
                }
            )

        ordered_trends.sort(key=lambda item: (item["category"], item["display_name"]))

        return {
            "ticker": company.ticker,
            "company_id": company.id,
            "calculation_version": CALCULATION_VERSION,
            "trends": ordered_trends,
        }

    def _refresh_metrics(self, company: Company) -> list[FinancialMetric]:
        self.db.query(FinancialMetric).filter(
            FinancialMetric.company_id == company.id,
            FinancialMetric.calculation_version == CALCULATION_VERSION,
        ).delete(synchronize_session=False)

        calculated_rows = self._calculate_metrics(company.id)
        self.db.add_all(calculated_rows)
        self.db.commit()

        return self._load_metric_rows(company.id)

    def _load_metric_rows(self, company_id: int) -> list[FinancialMetric]:
        return (
            self.db.query(FinancialMetric)
            .filter(
                FinancialMetric.company_id == company_id,
                FinancialMetric.calculation_version == CALCULATION_VERSION,
            )
            .order_by(
                FinancialMetric.fiscal_year.asc(),
                FinancialMetric.fiscal_period.asc(),
                FinancialMetric.metric_name.asc(),
            )
            .all()
        )

    def _calculate_metrics(self, company_id: int) -> list[FinancialMetric]:
        income_rows = (
            self.db.query(IncomeStatement)
            .filter(IncomeStatement.company_id == company_id)
            .all()
        )
        balance_rows = (
            self.db.query(BalanceSheet)
            .filter(BalanceSheet.company_id == company_id)
            .all()
        )
        cash_rows = (
            self.db.query(CashFlowStatement)
            .filter(CashFlowStatement.company_id == company_id)
            .all()
        )

        income_map = {(row.fiscal_year, row.fiscal_period): row for row in income_rows}
        balance_map = {(row.fiscal_year, row.fiscal_period): row for row in balance_rows}
        cash_map = {(row.fiscal_year, row.fiscal_period): row for row in cash_rows}

        period_keys = sorted(
            set(income_map.keys()) & set(balance_map.keys()) & set(cash_map.keys()),
            key=lambda key: (key[0], PERIOD_ORDER.get(key[1], 99)),
        )

        metric_rows: list[FinancialMetric] = []
        for fiscal_year, fiscal_period in period_keys:
            income = income_map[(fiscal_year, fiscal_period)]
            balance = balance_map[(fiscal_year, fiscal_period)]
            cash = cash_map[(fiscal_year, fiscal_period)]
            previous_key = (fiscal_year - 1, fiscal_period)
            prev_income = income_map.get(previous_key)
            prev_balance = balance_map.get(previous_key)
            prev_cash = cash_map.get(previous_key)

            period_type = PeriodType.annual if fiscal_period == "FY" else PeriodType.quarterly
            values = self._build_input_values(income, balance, cash)

            average_assets = self._average(balance.total_assets, prev_balance.total_assets if prev_balance else None)
            average_equity = self._average(balance.total_equity, prev_balance.total_equity if prev_balance else None)
            average_inventory = self._average(balance.inventory, prev_balance.inventory if prev_balance else None)
            average_receivables = self._average(
                balance.accounts_receivable,
                prev_balance.accounts_receivable if prev_balance else None,
            )

            pretax = self._to_decimal(income.pretax_income)
            tax_rate = self._safe_div(self._to_decimal(income.tax_expense), pretax)
            effective_tax_rate = tax_rate if tax_rate is not None else Decimal("0.21")
            nopat = self._to_decimal(income.operating_income) * (Decimal("1") - effective_tax_rate)
            invested_capital = (
                self._to_decimal(balance.total_debt)
                + self._to_decimal(balance.total_equity)
                - self._to_decimal(balance.cash_and_equivalents)
            )

            free_cash_flow = self._to_decimal(cash.cash_from_operations) - self._to_decimal(cash.capex)
            receivables_turnover = self._safe_div(self._to_decimal(income.revenue), average_receivables)
            inventory_turnover = self._safe_div(self._to_decimal(income.cogs), average_inventory)
            dso = self._safe_div(Decimal("365"), receivables_turnover)
            dio = self._safe_div(Decimal("365"), inventory_turnover)
            dpo = self._safe_div(
                Decimal("365") * self._to_decimal(balance.accounts_payable),
                self._to_decimal(income.cogs),
            )

            prior_fcf = None
            if prev_cash is not None:
                prior_fcf = self._to_decimal(prev_cash.cash_from_operations) - self._to_decimal(prev_cash.capex)

            period_metrics: dict[str, Decimal | None] = {
                "gross_margin": self._safe_div(self._to_decimal(income.gross_profit), self._to_decimal(income.revenue)),
                "operating_margin": self._safe_div(self._to_decimal(income.operating_income), self._to_decimal(income.revenue)),
                "net_margin": self._safe_div(self._to_decimal(income.net_income), self._to_decimal(income.revenue)),
                "ebitda_margin": self._safe_div(self._to_decimal(income.ebitda), self._to_decimal(income.revenue)),
                "roa": self._safe_div(self._to_decimal(income.net_income), average_assets),
                "roe": self._safe_div(self._to_decimal(income.net_income), average_equity),
                "roic": self._safe_div(nopat, invested_capital),
                "current_ratio": self._safe_div(self._to_decimal(balance.total_current_assets), self._to_decimal(balance.total_current_liabilities)),
                "quick_ratio": self._safe_div(
                    self._to_decimal(balance.total_current_assets) - self._to_decimal(balance.inventory),
                    self._to_decimal(balance.total_current_liabilities),
                ),
                "cash_ratio": self._safe_div(self._to_decimal(balance.cash), self._to_decimal(balance.total_current_liabilities)),
                "debt_to_equity": self._safe_div(self._to_decimal(balance.total_debt), self._to_decimal(balance.total_equity)),
                "debt_to_assets": self._safe_div(self._to_decimal(balance.total_debt), self._to_decimal(balance.total_assets)),
                "interest_coverage_ratio": self._safe_div(self._to_decimal(income.operating_income), abs(self._to_decimal(income.interest_expense))),
                "net_debt_to_ebitda": self._safe_div(
                    self._to_decimal(balance.total_debt) - self._to_decimal(balance.cash_and_equivalents),
                    self._to_decimal(income.ebitda),
                ),
                "asset_turnover": self._safe_div(self._to_decimal(income.revenue), average_assets),
                "inventory_turnover": inventory_turnover,
                "receivables_turnover": receivables_turnover,
                "dso": dso,
                "dio": dio,
                "ccc": None if dso is None or dio is None or dpo is None else dso + dio - dpo,
                "free_cash_flow": free_cash_flow,
                "free_cash_flow_margin": self._safe_div(free_cash_flow, self._to_decimal(income.revenue)),
                "cash_conversion_ratio": self._safe_div(self._to_decimal(cash.cash_from_operations), self._to_decimal(income.net_income)),
                "capex_as_pct_revenue": self._safe_div(self._to_decimal(cash.capex), self._to_decimal(income.revenue)),
                "revenue_growth_yoy": self._growth(self._to_decimal(income.revenue), self._to_decimal(prev_income.revenue) if prev_income else None),
                "gross_profit_growth_yoy": self._growth(self._to_decimal(income.gross_profit), self._to_decimal(prev_income.gross_profit) if prev_income else None),
                "operating_income_growth_yoy": self._growth(self._to_decimal(income.operating_income), self._to_decimal(prev_income.operating_income) if prev_income else None),
                "net_income_growth_yoy": self._growth(self._to_decimal(income.net_income), self._to_decimal(prev_income.net_income) if prev_income else None),
                "eps_growth_yoy": self._growth(self._to_decimal(income.eps), self._to_decimal(prev_income.eps) if prev_income else None),
                "free_cash_flow_growth_yoy": self._growth(free_cash_flow, prior_fcf),
            }

            for metric_name, metric_value in period_metrics.items():
                definition = METRIC_DEFINITIONS[metric_name]
                metric_rows.append(
                    FinancialMetric(
                        company_id=company_id,
                        fiscal_year=fiscal_year,
                        fiscal_period=fiscal_period,
                        period_type=period_type,
                        metric_name=metric_name,
                        metric_value=metric_value,
                        formula=definition.formula,
                        inputs_used=self._inputs_snapshot(metric_name, values, prev_income, prev_cash),
                        source_metrics=definition.source_metrics,
                        calculation_version=CALCULATION_VERSION,
                    )
                )

        return metric_rows

    def _inputs_snapshot(
        self,
        metric_name: str,
        values: dict[str, Decimal],
        prev_income: IncomeStatement | None,
        prev_cash: CashFlowStatement | None,
    ) -> dict[str, float | int | None]:
        source_keys = METRIC_DEFINITIONS[metric_name].source_metrics
        snapshot: dict[str, float | int | None] = {}
        for key in source_keys:
            if key.startswith("prior_year_"):
                prior_field = key.replace("prior_year_", "")
                if prior_field == "free_cash_flow":
                    if prev_cash is None:
                        snapshot[key] = None
                    else:
                        prior_fcf = self._to_decimal(prev_cash.cash_from_operations) - self._to_decimal(prev_cash.capex)
                        snapshot[key] = float(prior_fcf)
                elif prev_income is None:
                    snapshot[key] = None
                else:
                    snapshot[key] = float(self._to_decimal(getattr(prev_income, prior_field)))
                continue
            snapshot[key] = float(values.get(key)) if key in values else None
        return snapshot

    def _build_input_values(self, income: IncomeStatement, balance: BalanceSheet, cash: CashFlowStatement) -> dict[str, Decimal]:
        return {
            "revenue": self._to_decimal(income.revenue),
            "gross_profit": self._to_decimal(income.gross_profit),
            "operating_income": self._to_decimal(income.operating_income),
            "net_income": self._to_decimal(income.net_income),
            "ebitda": self._to_decimal(income.ebitda),
            "tax_expense": self._to_decimal(income.tax_expense),
            "pretax_income": self._to_decimal(income.pretax_income),
            "interest_expense": self._to_decimal(income.interest_expense),
            "eps": self._to_decimal(income.eps),
            "cogs": self._to_decimal(income.cogs),
            "total_current_assets": self._to_decimal(balance.total_current_assets),
            "inventory": self._to_decimal(balance.inventory),
            "total_current_liabilities": self._to_decimal(balance.total_current_liabilities),
            "cash": self._to_decimal(balance.cash),
            "total_debt": self._to_decimal(balance.total_debt),
            "total_assets": self._to_decimal(balance.total_assets),
            "total_equity": self._to_decimal(balance.total_equity),
            "cash_and_equivalents": self._to_decimal(balance.cash_and_equivalents),
            "accounts_receivable": self._to_decimal(balance.accounts_receivable),
            "accounts_payable": self._to_decimal(balance.accounts_payable),
            "cash_from_operations": self._to_decimal(cash.cash_from_operations),
            "capex": self._to_decimal(cash.capex),
            "free_cash_flow": self._to_decimal(cash.cash_from_operations) - self._to_decimal(cash.capex),
        }

    def _build_historical_periods(self, metric_rows: list[FinancialMetric]) -> list[dict[str, Any]]:
        by_period: dict[tuple[int, str], dict[str, Decimal | None]] = defaultdict(dict)
        for row in metric_rows:
            by_period[(row.fiscal_year, row.fiscal_period)][row.metric_name] = row.metric_value

        periods = []
        for key in sorted(by_period.keys(), key=lambda item: (item[0], PERIOD_ORDER.get(item[1], 99))):
            fiscal_year, fiscal_period = key
            periods.append(
                {
                    "fiscal_year": fiscal_year,
                    "fiscal_period": fiscal_period,
                    "metrics": by_period[key],
                }
            )
        return periods

    def _group_metric_rows(self, metric_rows: list[FinancialMetric]) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in metric_rows:
            grouped[row.metric_name].append(
                {
                    "fiscal_year": row.fiscal_year,
                    "fiscal_period": row.fiscal_period,
                    "metric_value": row.metric_value,
                }
            )

        for metric_name in grouped:
            grouped[metric_name].sort(key=lambda item: (item["fiscal_year"], PERIOD_ORDER.get(item["fiscal_period"], 99)))
        return grouped

    def _compute_trends(self, grouped: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Decimal | str | None]]:
        trends: dict[str, dict[str, Decimal | str | None]] = {}

        for metric_name, series in grouped.items():
            values = [item["metric_value"] for item in series if item["metric_value"] is not None]
            latest_value = values[-1] if values else None
            previous_value = values[-2] if len(values) >= 2 else None
            cagr_3y = self._cagr(values, 3)
            cagr_5y = self._cagr(values, 5)
            rolling_avg = self._rolling_average(values, 3)
            directionality = ratio_direction(metric_name)
            trend_direction = self._trend_direction(latest_value, previous_value, directionality)

            trends[metric_name] = {
                "latest_value": latest_value,
                "previous_value": previous_value,
                "cagr_3y": cagr_3y,
                "cagr_5y": cagr_5y,
                "rolling_average_3_periods": rolling_avg,
                "trend_direction": trend_direction,
            }

        return trends

    def _cagr(self, values: list[Decimal], periods: int) -> Decimal | None:
        if len(values) < periods + 1:
            return None

        start = values[-(periods + 1)]
        end = values[-1]
        if start is None or end is None:
            return None
        if start <= 0 or end <= 0:
            return None

        start_f = float(start)
        end_f = float(end)
        ratio = end_f / start_f
        if not isfinite(ratio) or ratio <= 0:
            return None

        value = (ratio ** (1.0 / periods)) - 1.0
        return Decimal(str(value))

    def _rolling_average(self, values: list[Decimal], window: int) -> Decimal | None:
        if len(values) < window:
            return None
        subset = values[-window:]
        total = sum(subset, start=Decimal("0"))
        return total / Decimal(str(window))

    def _trend_direction(
        self,
        latest: Decimal | None,
        previous: Decimal | None,
        directionality: str,
    ) -> str | None:
        if latest is None or previous is None:
            return None
        baseline = abs(previous) if previous != 0 else Decimal("1")
        delta = latest - previous
        delta_pct = delta / baseline

        if abs(delta_pct) <= Decimal("0.02"):
            return "Stable"

        if directionality == "lower":
            return "Improving" if delta_pct < 0 else "Deteriorating"
        return "Improving" if delta_pct > 0 else "Deteriorating"

    def _get_company(self, ticker: str) -> Company | None:
        return self.db.query(Company).filter(Company.ticker == ticker.upper()).one_or_none()

    def _safe_div(self, numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
        if numerator is None or denominator is None:
            return None
        if denominator == 0:
            return None
        return numerator / denominator

    def _growth(self, current: Decimal | None, previous: Decimal | None) -> Decimal | None:
        if current is None or previous is None:
            return None
        if previous == 0:
            return None
        return (current - previous) / abs(previous)

    def _average(self, current: Decimal, previous: Decimal | None) -> Decimal:
        if previous is None:
            return current
        return (current + previous) / Decimal("2")

    def _to_decimal(self, value: Any) -> Decimal:
        return Decimal(str(value))
