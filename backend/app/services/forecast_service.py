from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.balance_sheet import BalanceSheet
from app.models.cash_flow_statement import CashFlowStatement
from app.models.company import Company
from app.models.financial_metric import FinancialMetric
from app.models.forecast_assumptions import ForecastAssumptionSet
from app.models.guidance_record import GuidanceRecord
from app.models.income_statement import IncomeStatement
from app.models.news_event import NewsEvent
from app.models.research_risk import ResearchRisk


ScenarioName = str


DEFAULT_SCENARIO_OVERRIDES: dict[str, dict[str, float]] = {
    "base": {
        "revenue_growth_delta": 0.0,
        "margin_delta": 0.0,
        "working_capital_delta": 0.0,
        "capex_delta": 0.0,
        "interest_rate_delta": 0.0,
    },
    "bull": {
        "revenue_growth_delta": 0.02,
        "margin_delta": 0.01,
        "working_capital_delta": -2.0,
        "capex_delta": -0.005,
        "interest_rate_delta": -0.003,
    },
    "bear": {
        "revenue_growth_delta": -0.03,
        "margin_delta": -0.015,
        "working_capital_delta": 3.0,
        "capex_delta": 0.01,
        "interest_rate_delta": 0.004,
    },
}


@dataclass
class HistoricalSnapshot:
    company: Company
    income: IncomeStatement
    balance: BalanceSheet
    cash_flow: CashFlowStatement


def d(value: float | Decimal | int) -> Decimal:
    return Decimal(str(value))


class ForecastService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_scenarios(self) -> list[str]:
        return ["base", "bull", "bear"]

    def get_forecast_payload(
        self,
        ticker: str,
        scenario: ScenarioName = "base",
        assumptions_version: str = "latest",
        horizon_years: int | None = None,
        assumptions_override: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        company = self._get_company(ticker)
        if company is None:
            return None

        snapshot = self._latest_snapshot(company.id)
        if snapshot is None:
            return None

        assumptions_record = self._resolve_assumptions(company.id, assumptions_version, scenario, snapshot)
        assumptions = dict(assumptions_record.assumptions)
        if assumptions_override:
            assumptions = self._deep_merge(assumptions, assumptions_override)

        horizon = int(horizon_years or assumptions.get("meta", {}).get("horizon_years", 7))
        horizon = max(5, min(10, horizon))

        projections = self._project_statements(snapshot, assumptions, scenario, horizon)
        validation = self._validate_forecast(projections)

        return {
            "ticker": company.ticker,
            "company_id": company.id,
            "scenario": scenario,
            "assumptions_version": assumptions_record.version,
            "generated_at": datetime.now(timezone.utc),
            "assumptions": assumptions,
            "validation": validation,
            "projections": projections,
        }

    def get_all_scenarios_payload(
        self,
        ticker: str,
        assumptions_version: str = "latest",
        horizon_years: int | None = None,
        assumptions_override: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        company = self._get_company(ticker)
        if company is None:
            return None

        scenarios: dict[str, Any] = {}
        generated_at = datetime.now(timezone.utc)
        resolved_version = assumptions_version
        for scenario in self.list_scenarios():
            payload = self.get_forecast_payload(
                ticker=ticker,
                scenario=scenario,
                assumptions_version=assumptions_version,
                horizon_years=horizon_years,
                assumptions_override=assumptions_override,
            )
            if payload is None:
                continue
            resolved_version = payload["assumptions_version"]
            scenarios[scenario] = payload

        if not scenarios:
            return None

        return {
            "ticker": company.ticker,
            "company_id": company.id,
            "assumptions_version": resolved_version,
            "generated_at": generated_at,
            "scenarios": scenarios,
        }

    def _get_company(self, ticker: str) -> Company | None:
        return self.db.query(Company).filter(Company.ticker == ticker.upper()).one_or_none()

    def _latest_snapshot(self, company_id: int) -> HistoricalSnapshot | None:
        income = (
            self.db.query(IncomeStatement)
            .filter(IncomeStatement.company_id == company_id)
            .order_by(IncomeStatement.fiscal_year.desc(), IncomeStatement.fiscal_period.desc())
            .first()
        )
        balance = (
            self.db.query(BalanceSheet)
            .filter(BalanceSheet.company_id == company_id)
            .order_by(BalanceSheet.fiscal_year.desc(), BalanceSheet.fiscal_period.desc())
            .first()
        )
        cash_flow = (
            self.db.query(CashFlowStatement)
            .filter(CashFlowStatement.company_id == company_id)
            .order_by(CashFlowStatement.fiscal_year.desc(), CashFlowStatement.fiscal_period.desc())
            .first()
        )

        if not income or not balance or not cash_flow:
            return None

        company = self.db.query(Company).filter(Company.id == company_id).one()
        return HistoricalSnapshot(company=company, income=income, balance=balance, cash_flow=cash_flow)

    def _resolve_assumptions(
        self,
        company_id: int,
        assumptions_version: str,
        scenario: ScenarioName,
        snapshot: HistoricalSnapshot,
    ) -> ForecastAssumptionSet:
        record: ForecastAssumptionSet | None
        query = self.db.query(ForecastAssumptionSet).filter(
            ForecastAssumptionSet.company_id == company_id,
            ForecastAssumptionSet.scenario == scenario,
        )
        if assumptions_version == "latest":
            record = query.order_by(ForecastAssumptionSet.created_at.desc()).first()
        else:
            record = query.filter(ForecastAssumptionSet.version == assumptions_version).one_or_none()

        if record:
            return record

        synthesized = self._synthesize_default_assumptions(snapshot, scenario)
        version = assumptions_version if assumptions_version != "latest" else "v1"
        record = ForecastAssumptionSet(
            company_id=company_id,
            version=version,
            scenario=scenario,
            is_active=True,
            assumptions=synthesized,
            source_context=self._source_context(snapshot.company.id),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def _source_context(self, company_id: int) -> dict[str, Any]:
        latest_guidance = (
            self.db.query(GuidanceRecord)
            .filter(GuidanceRecord.company_id == company_id)
            .order_by(GuidanceRecord.publication_date.desc())
            .limit(5)
            .all()
        )
        latest_risks = (
            self.db.query(ResearchRisk)
            .filter(ResearchRisk.company_id == company_id)
            .order_by(ResearchRisk.publication_date.desc())
            .limit(5)
            .all()
        )
        latest_news = (
            self.db.query(NewsEvent)
            .filter(NewsEvent.company_id == company_id)
            .order_by(NewsEvent.publication_date.desc())
            .limit(5)
            .all()
        )

        return {
            "guidance_count": len(latest_guidance),
            "risk_count": len(latest_risks),
            "news_count": len(latest_news),
            "negative_news_count": sum(1 for item in latest_news if item.sentiment.lower() == "negative"),
        }

    def _synthesize_default_assumptions(self, snapshot: HistoricalSnapshot, scenario: ScenarioName) -> dict[str, Any]:
        growth = d(snapshot.income.revenue) / d(max(d(snapshot.income.revenue), d(1)))
        gross_margin = d(snapshot.income.gross_profit) / d(max(d(snapshot.income.revenue), d(1)))
        operating_margin = d(snapshot.income.operating_income) / d(max(d(snapshot.income.revenue), d(1)))

        capex_ratio = d(snapshot.cash_flow.capex) / d(max(d(snapshot.income.revenue), d(1)))
        dep_ratio = d(snapshot.income.depreciation_and_amortization) / d(max(d(snapshot.income.revenue), d(1)))

        dso = d(snapshot.balance.accounts_receivable) / d(max(d(snapshot.income.revenue), d(1))) * d(365)
        dio = d(snapshot.balance.inventory) / d(max(d(snapshot.income.cogs), d(1))) * d(365)
        dpo = d(snapshot.balance.accounts_payable) / d(max(d(snapshot.income.cogs), d(1))) * d(365)

        tax_rate = d(snapshot.income.tax_expense) / d(max(d(snapshot.income.pretax_income), d(1)))
        debt_interest_rate = d(snapshot.income.interest_expense) / d(max(d(snapshot.balance.total_debt), d(1)))
        share_count = d(snapshot.income.net_income) / d(max(d(snapshot.income.eps), d(0.01)))

        override = DEFAULT_SCENARIO_OVERRIDES.get(scenario, DEFAULT_SCENARIO_OVERRIDES["base"])

        revenue_growth = float(max(d(-0.5), min(d(0.5), d("0.06") + d(str(override["revenue_growth_delta"])))) )

        return {
            "meta": {
                "horizon_years": 7,
                "version_description": "Auto-generated from latest history and research context",
            },
            "revenue_drivers": {
                "revenue_growth_by_year": [revenue_growth] * 10,
                "segment_growth": {},
                "pricing_effect": 0.0,
                "volume_effect": 0.0,
            },
            "margin_drivers": {
                "gross_margin_pct": float(max(d(0.05), min(d(0.9), gross_margin + d(str(override["margin_delta"]))))),
                "operating_margin_pct": float(max(d(-0.2), min(d(0.7), operating_margin + d(str(override["margin_delta"]))))),
                "sga_pct_revenue": float(max(d(0), min(d(0.8), d(0.18) - d(str(override["margin_delta"])) / d(2)))),
                "rnd_pct_revenue": float(max(d(0), min(d(0.5), d(0.08)))),
            },
            "cash_flow_drivers": {
                "capex_pct_revenue": float(max(d(0), min(d(0.5), capex_ratio + d(str(override["capex_delta"]))))),
                "depreciation_pct_revenue": float(max(d(0), min(d(0.4), dep_ratio))),
                "dso_days": float(max(d(5), min(d(240), dso + d(str(override["working_capital_delta"]))))),
                "dio_days": float(max(d(5), min(d(300), dio + d(str(override["working_capital_delta"]))))),
                "dpo_days": float(max(d(5), min(d(240), dpo + d(str(override["working_capital_delta"]))))),
            },
            "tax_and_capital": {
                "effective_tax_rate": float(max(d(0), min(d(0.6), tax_rate))),
                "debt_interest_rate": float(max(d(0), min(d(0.4), debt_interest_rate + d(str(override["interest_rate_delta"]))))),
                "share_count_start": float(max(d(1), share_count)),
                "share_count_change_pct": 0.0,
                "target_min_cash": float(max(d(0), d(snapshot.balance.cash) * d(0.03))),
                "target_max_debt_to_ebitda": 4.0,
            },
            "financing_policy": {
                "share_buybacks_pct_fcf": 0.1,
                "share_issuance_amount": 0.0,
                "debt_repayment_pct_fcf": 0.15,
                "allow_new_debt": True,
            },
        }

    def _project_statements(
        self,
        snapshot: HistoricalSnapshot,
        assumptions: dict[str, Any],
        scenario: ScenarioName,
        horizon: int,
    ) -> list[dict[str, Any]]:
        rev_growth_by_year = assumptions["revenue_drivers"]["revenue_growth_by_year"]
        margin = assumptions["margin_drivers"]
        cash_drivers = assumptions["cash_flow_drivers"]
        tax_cap = assumptions["tax_and_capital"]
        financing_policy = assumptions["financing_policy"]

        prev_revenue = d(snapshot.income.revenue)
        prev_ar = d(snapshot.balance.accounts_receivable)
        prev_inventory = d(snapshot.balance.inventory)
        prev_ap = d(snapshot.balance.accounts_payable)
        prev_cash = d(snapshot.balance.cash)
        prev_debt = d(snapshot.balance.total_debt)
        prev_equity = d(snapshot.balance.total_equity)
        share_count = d(tax_cap["share_count_start"])

        projections: list[dict[str, Any]] = []

        for i in range(horizon):
            fiscal_year = int(snapshot.income.fiscal_year) + i + 1
            growth = d(rev_growth_by_year[min(i, len(rev_growth_by_year) - 1)])

            revenue = prev_revenue * (d(1) + growth)
            gross_profit = revenue * d(margin["gross_margin_pct"])
            cogs = revenue - gross_profit

            sga = revenue * d(margin["sga_pct_revenue"])
            rnd = revenue * d(margin["rnd_pct_revenue"])
            operating_expenses = sga + rnd

            operating_income = revenue * d(margin["operating_margin_pct"])
            depreciation = revenue * d(cash_drivers["depreciation_pct_revenue"])
            capex = revenue * d(cash_drivers["capex_pct_revenue"])

            ar = revenue * d(cash_drivers["dso_days"]) / d(365)
            inventory = cogs * d(cash_drivers["dio_days"]) / d(365)
            ap = cogs * d(cash_drivers["dpo_days"]) / d(365)
            delta_wc = (ar - prev_ar) + (inventory - prev_inventory) - (ap - prev_ap)

            debt = prev_debt
            interest_expense = d(0)
            debt_issued = d(0)
            debt_repaid = d(0)
            share_issuance = d(financing_policy["share_issuance_amount"])
            share_buybacks = d(0)

            converged = False
            for _ in range(20):
                interest_expense = debt * d(tax_cap["debt_interest_rate"])
                pretax_income = operating_income - interest_expense
                tax_expense = max(d(0), pretax_income * d(tax_cap["effective_tax_rate"]))
                net_income = pretax_income - tax_expense

                operating_cash_flow = net_income + depreciation - delta_wc
                investing_cash_flow = -capex

                free_cash_flow = operating_cash_flow + investing_cash_flow

                if free_cash_flow > d(0):
                    debt_repaid = free_cash_flow * d(financing_policy["debt_repayment_pct_fcf"])
                    if debt_repaid > debt:
                        debt_repaid = debt
                    share_buybacks = free_cash_flow * d(financing_policy["share_buybacks_pct_fcf"])
                    debt_issued = d(0)
                else:
                    debt_repaid = d(0)
                    share_buybacks = d(0)
                    debt_issued = -free_cash_flow if financing_policy.get("allow_new_debt", True) else d(0)

                financing_cash_flow = debt_issued - debt_repaid + share_issuance - share_buybacks
                net_change_cash = free_cash_flow + financing_cash_flow
                ending_cash = prev_cash + net_change_cash

                min_cash = d(tax_cap["target_min_cash"])
                if ending_cash < min_cash and financing_policy.get("allow_new_debt", True):
                    top_up = min_cash - ending_cash
                    debt_issued += top_up
                    financing_cash_flow += top_up
                    net_change_cash += top_up
                    ending_cash = min_cash

                new_debt = max(d(0), prev_debt + debt_issued - debt_repaid)
                if abs(new_debt - debt) < d("0.0001"):
                    debt = new_debt
                    converged = True
                    break
                debt = new_debt

            interest_expense = debt * d(tax_cap["debt_interest_rate"])
            pretax_income = operating_income - interest_expense
            tax_expense = max(d(0), pretax_income * d(tax_cap["effective_tax_rate"]))
            net_income = pretax_income - tax_expense
            operating_cash_flow = net_income + depreciation - delta_wc
            investing_cash_flow = -capex
            free_cash_flow = operating_cash_flow + investing_cash_flow
            financing_cash_flow = debt_issued - debt_repaid + share_issuance - share_buybacks
            net_change_cash = free_cash_flow + financing_cash_flow
            ending_cash = max(d(0), prev_cash + net_change_cash)

            share_count = max(d(1), share_count * (d(1) + d(tax_cap["share_count_change_pct"])))
            if share_buybacks > d(0):
                share_count = max(d(1), share_count - (share_buybacks / d(max(net_income, d(1)))))
            eps = net_income / d(max(share_count, d(1)))

            total_assets = ending_cash + ar + inventory
            total_liabilities = ap + debt
            equity = prev_equity + net_income + share_issuance - share_buybacks
            if total_assets < total_liabilities + equity:
                total_assets = total_liabilities + equity
            balance_delta = total_assets - (total_liabilities + equity)
            if balance_delta != d(0):
                ending_cash -= balance_delta
                total_assets = ending_cash + ar + inventory
                if total_assets < total_liabilities + equity:
                    total_assets = total_liabilities + equity

            explainability = {
                "revenue": {
                    "formula": "prev_revenue * (1 + growth_rate)",
                    "inputs": {"prev_revenue": float(prev_revenue), "growth_rate": float(growth)},
                    "source_historical_metric": "income_statements.revenue",
                    "scenario_override": scenario != "base",
                },
                "gross_profit": {
                    "formula": "revenue * gross_margin_pct",
                    "inputs": {"revenue": float(revenue), "gross_margin_pct": margin["gross_margin_pct"]},
                    "source_historical_metric": "income_statements.gross_profit",
                    "scenario_override": scenario != "base",
                },
                "operating_income": {
                    "formula": "revenue * operating_margin_pct",
                    "inputs": {"revenue": float(revenue), "operating_margin_pct": margin["operating_margin_pct"]},
                    "source_historical_metric": "income_statements.operating_income",
                    "scenario_override": scenario != "base",
                },
                "interest_expense": {
                    "formula": "avg_debt * debt_interest_rate (iterative)",
                    "inputs": {"debt": float(debt), "debt_interest_rate": tax_cap["debt_interest_rate"], "converged": converged},
                    "source_historical_metric": "income_statements.interest_expense",
                    "scenario_override": scenario != "base",
                },
                "accounts_receivable": {
                    "formula": "revenue * dso / 365",
                    "inputs": {"revenue": float(revenue), "dso": cash_drivers["dso_days"]},
                    "source_historical_metric": "balance_sheets.accounts_receivable",
                    "scenario_override": scenario != "base",
                },
                "inventory": {
                    "formula": "cogs * dio / 365",
                    "inputs": {"cogs": float(cogs), "dio": cash_drivers["dio_days"]},
                    "source_historical_metric": "balance_sheets.inventory",
                    "scenario_override": scenario != "base",
                },
                "accounts_payable": {
                    "formula": "cogs * dpo / 365",
                    "inputs": {"cogs": float(cogs), "dpo": cash_drivers["dpo_days"]},
                    "source_historical_metric": "balance_sheets.accounts_payable",
                    "scenario_override": scenario != "base",
                },
                "operating_cash_flow": {
                    "formula": "net_income + depreciation - change_in_working_capital",
                    "inputs": {
                        "net_income": float(net_income),
                        "depreciation": float(depreciation),
                        "change_in_working_capital": float(delta_wc),
                    },
                    "source_historical_metric": "cash_flow_statements.cash_from_operations",
                    "scenario_override": scenario != "base",
                },
                "ending_cash_balance": {
                    "formula": "prev_cash + free_cash_flow + financing_cash_flow",
                    "inputs": {
                        "prev_cash": float(prev_cash),
                        "free_cash_flow": float(free_cash_flow),
                        "financing_cash_flow": float(financing_cash_flow),
                    },
                    "source_historical_metric": "cash_flow_statements.ending_cash",
                    "scenario_override": scenario != "base",
                },
            }

            projections.append(
                {
                    "fiscal_year": fiscal_year,
                    "scenario": scenario,
                    "income_statement": {
                        "revenue": float(revenue),
                        "cogs": float(cogs),
                        "gross_profit": float(gross_profit),
                        "operating_expenses": float(operating_expenses),
                        "operating_income": float(operating_income),
                        "interest_expense": float(interest_expense),
                        "pretax_income": float(pretax_income),
                        "tax_expense": float(tax_expense),
                        "net_income": float(net_income),
                        "eps": float(eps),
                    },
                    "balance_sheet": {
                        "cash": float(ending_cash),
                        "accounts_receivable": float(ar),
                        "inventory": float(inventory),
                        "accounts_payable": float(ap),
                        "total_assets": float(total_assets),
                        "total_liabilities": float(total_liabilities),
                        "shareholder_equity": float(equity),
                        "total_debt": float(debt),
                    },
                    "cash_flow_statement": {
                        "net_income": float(net_income),
                        "depreciation_and_amortization": float(depreciation),
                        "change_in_working_capital": float(delta_wc),
                        "operating_cash_flow": float(operating_cash_flow),
                        "capex": float(capex),
                        "investing_cash_flow": float(investing_cash_flow),
                        "debt_issued": float(debt_issued),
                        "debt_repaid": float(debt_repaid),
                        "share_issuance": float(share_issuance),
                        "share_buybacks": float(share_buybacks),
                        "financing_cash_flow": float(financing_cash_flow),
                        "free_cash_flow": float(free_cash_flow),
                        "ending_cash_balance": float(ending_cash),
                    },
                    "explainability": explainability,
                }
            )

            prev_revenue = revenue
            prev_ar = ar
            prev_inventory = inventory
            prev_ap = ap
            prev_cash = ending_cash
            prev_debt = debt
            prev_equity = equity

        return projections

    def _validate_forecast(self, projections: list[dict[str, Any]]) -> dict[str, Any]:
        negative_asset_warnings: list[str] = []
        unreasonable_growth_flags: list[str] = []
        margin_sanity_flags: list[str] = []
        notes: list[str] = []

        balance_sheet_balanced = True
        cash_rollforward_reconciled = True

        prev_revenue: float | None = None
        for period in projections:
            year = period["fiscal_year"]
            income = period["income_statement"]
            balance = period["balance_sheet"]
            cash = period["cash_flow_statement"]

            lhs = d(balance["total_assets"])
            rhs = d(balance["total_liabilities"]) + d(balance["shareholder_equity"])
            if abs(lhs - rhs) > d("0.01"):
                balance_sheet_balanced = False
                notes.append(f"{year}: balance sheet mismatch {float(lhs - rhs):.2f}")

            computed_cash = d(cash["ending_cash_balance"])
            if computed_cash < d(0):
                negative_asset_warnings.append(f"{year}: ending cash is negative ({float(computed_cash):.2f})")

            if d(balance["accounts_receivable"]) < d(0) or d(balance["inventory"]) < d(0):
                negative_asset_warnings.append(f"{year}: receivables/inventory became negative.")

            ocf = d(cash["operating_cash_flow"])
            fcf = d(cash["free_cash_flow"])
            capex = d(cash["capex"])
            if abs((ocf - capex) - fcf) > d("0.05"):
                cash_rollforward_reconciled = False
                notes.append(f"{year}: free cash flow does not reconcile with OCF-CapEx")

            revenue = d(income["revenue"])
            if prev_revenue is not None and prev_revenue > 0:
                growth = (float(revenue) - prev_revenue) / abs(prev_revenue)
                if growth > 0.5 or growth < -0.4:
                    unreasonable_growth_flags.append(f"{year}: revenue growth {growth * 100:.1f}% outside expected band")
            prev_revenue = float(revenue)

            gross_margin = d(income["gross_profit"]) / d(max(revenue, d(1)))
            operating_margin = d(income["operating_income"]) / d(max(revenue, d(1)))
            if gross_margin < d(0) or gross_margin > d(0.9):
                margin_sanity_flags.append(f"{year}: gross margin {float(gross_margin) * 100:.1f}% outside sanity range")
            if operating_margin < d(-0.3) or operating_margin > d(0.6):
                margin_sanity_flags.append(f"{year}: operating margin {float(operating_margin) * 100:.1f}% outside sanity range")

        return {
            "balance_sheet_balanced": balance_sheet_balanced,
            "cash_rollforward_reconciled": cash_rollforward_reconciled,
            "negative_asset_warnings": negative_asset_warnings,
            "unreasonable_growth_flags": unreasonable_growth_flags,
            "margin_sanity_flags": margin_sanity_flags,
            "notes": notes,
        }

    def _deep_merge(self, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
        merged = dict(left)
        for key, value in right.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = self._deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged
