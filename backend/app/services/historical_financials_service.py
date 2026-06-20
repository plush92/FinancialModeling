from __future__ import annotations

from decimal import Decimal
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.mappings.sec_xbrl_mappings import CANONICAL_TAG_MAPPINGS, USD_UNIT_METRICS
from app.models.balance_sheet import BalanceSheet
from app.models.cash_flow_statement import CashFlowStatement
from app.models.company import Company
from app.models.income_statement import IncomeStatement
from app.services.financials_validation_service import FinancialsValidationService
from app.services.sec_client import SECClient


class HistoricalFinancialsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.sec_client = SECClient()
        self.validator = FinancialsValidationService(db)

    def get_company(self, ticker: str) -> Company | None:
        return self.db.query(Company).filter(Company.ticker == ticker.upper()).one_or_none()

    def get_financials_bundle(self, ticker: str) -> dict[str, Any] | None:
        company = self.get_company(ticker)
        if company is None:
            return None

        income_rows = (
            self.db.query(IncomeStatement)
            .filter(IncomeStatement.company_id == company.id)
            .order_by(IncomeStatement.fiscal_year.desc(), IncomeStatement.fiscal_period.desc())
            .all()
        )
        balance_rows = (
            self.db.query(BalanceSheet)
            .filter(BalanceSheet.company_id == company.id)
            .order_by(BalanceSheet.fiscal_year.desc(), BalanceSheet.fiscal_period.desc())
            .all()
        )
        cash_rows = (
            self.db.query(CashFlowStatement)
            .filter(CashFlowStatement.company_id == company.id)
            .order_by(CashFlowStatement.fiscal_year.desc(), CashFlowStatement.fiscal_period.desc())
            .all()
        )

        return {
            "company": company,
            "income_statements": income_rows,
            "balance_sheets": balance_rows,
            "cash_flow_statements": cash_rows,
        }

    def sync_ticker(self, ticker: str, max_periods: int = 8) -> dict[str, Any]:
        normalized_ticker = ticker.upper().strip()
        cik = self.sec_client.resolve_cik(normalized_ticker)
        submissions = self.sec_client.get_submissions(cik)
        facts = self.sec_client.get_company_facts(cik)

        company = self._upsert_company(normalized_ticker, cik, submissions)
        periods = self._extract_periods(submissions, max_periods=max_periods)

        synced_income = 0
        synced_balance = 0
        synced_cash_flow = 0

        for period in periods:
            fiscal_year = period["fiscal_year"]
            fiscal_period = period["fiscal_period"]
            form = period["form"]
            accession = period["accession_number"]

            if not self.validator.validate_fiscal_year(normalized_ticker, fiscal_year, company.id):
                continue

            extracted = self._extract_period_values(facts, fiscal_year, fiscal_period, form, accession)

            income_values = extracted["income_statement"]
            if not self.validator.is_duplicate_period(IncomeStatement, company.id, fiscal_year, fiscal_period):
                self.validator.validate_required_values(
                    normalized_ticker,
                    "income_statement",
                    fiscal_year,
                    fiscal_period,
                    {
                        "revenue": income_values.get("revenue"),
                        "gross_profit": income_values.get("gross_profit"),
                        "operating_income": income_values.get("operating_income"),
                        "net_income": income_values.get("net_income"),
                        "eps": income_values.get("eps"),
                    },
                    company.id,
                )
                self.db.add(
                    IncomeStatement(
                        company_id=company.id,
                        fiscal_year=fiscal_year,
                        fiscal_period=fiscal_period,
                        period_type="annual" if fiscal_period == "FY" else "quarterly",
                        currency="USD",
                        source_form=form,
                        source_accession_number=accession,
                        revenue=income_values.get("revenue") or Decimal("0"),
                        cogs=Decimal("0"),
                        gross_profit=income_values.get("gross_profit") or Decimal("0"),
                        operating_expenses=Decimal("0"),
                        ebitda=income_values.get("operating_income") or Decimal("0"),
                        depreciation_and_amortization=Decimal("0"),
                        operating_income=income_values.get("operating_income") or Decimal("0"),
                        interest_expense=Decimal("0"),
                        pretax_income=income_values.get("net_income") or Decimal("0"),
                        tax_expense=Decimal("0"),
                        net_income=income_values.get("net_income") or Decimal("0"),
                        eps=income_values.get("eps") or Decimal("0"),
                    )
                )
                synced_income += 1
            else:
                self.validator.log_warning(
                    normalized_ticker,
                    "duplicate_period",
                    f"Skipped duplicate income statement for {fiscal_year}-{fiscal_period}.",
                    company.id,
                )

            balance_values = extracted["balance_sheet"]
            if not self.validator.is_duplicate_period(BalanceSheet, company.id, fiscal_year, fiscal_period):
                total_assets = balance_values.get("total_assets") or Decimal("0")
                total_liabilities = balance_values.get("total_liabilities") or Decimal("0")
                shareholder_equity = balance_values.get("shareholder_equity") or Decimal("0")
                self.validator.validate_required_values(
                    normalized_ticker,
                    "balance_sheet",
                    fiscal_year,
                    fiscal_period,
                    {
                        "cash": balance_values.get("cash"),
                        "total_assets": balance_values.get("total_assets"),
                        "total_liabilities": balance_values.get("total_liabilities"),
                        "shareholder_equity": balance_values.get("shareholder_equity"),
                        "total_debt": balance_values.get("total_debt"),
                    },
                    company.id,
                )
                self.validator.validate_balance_sheet_equation(
                    normalized_ticker,
                    fiscal_year,
                    fiscal_period,
                    total_assets,
                    total_liabilities,
                    shareholder_equity,
                    company.id,
                )
                self.db.add(
                    BalanceSheet(
                        company_id=company.id,
                        fiscal_year=fiscal_year,
                        fiscal_period=fiscal_period,
                        period_type="annual" if fiscal_period == "FY" else "quarterly",
                        currency="USD",
                        source_form=form,
                        source_accession_number=accession,
                        cash=balance_values.get("cash") or Decimal("0"),
                        total_assets=total_assets,
                        total_liabilities=total_liabilities,
                        shareholder_equity=shareholder_equity,
                        total_debt=balance_values.get("total_debt") or Decimal("0"),
                        cash_and_equivalents=balance_values.get("cash") or Decimal("0"),
                        accounts_receivable=Decimal("0"),
                        inventory=Decimal("0"),
                        total_current_assets=balance_values.get("cash") or Decimal("0"),
                        property_plant_equipment=Decimal("0"),
                        accounts_payable=Decimal("0"),
                        short_term_debt=Decimal("0"),
                        total_current_liabilities=Decimal("0"),
                        long_term_debt=balance_values.get("total_debt") or Decimal("0"),
                        total_equity=shareholder_equity,
                    )
                )
                synced_balance += 1
            else:
                self.validator.log_warning(
                    normalized_ticker,
                    "duplicate_period",
                    f"Skipped duplicate balance sheet for {fiscal_year}-{fiscal_period}.",
                    company.id,
                )

            cash_values = extracted["cash_flow_statement"]
            if not self.validator.is_duplicate_period(CashFlowStatement, company.id, fiscal_year, fiscal_period):
                operating_cash_flow = cash_values.get("operating_cash_flow") or Decimal("0")
                capex = cash_values.get("capex") or Decimal("0")
                free_cash_flow = cash_values.get("free_cash_flow")
                if free_cash_flow is None:
                    free_cash_flow = operating_cash_flow - capex

                self.validator.validate_required_values(
                    normalized_ticker,
                    "cash_flow_statement",
                    fiscal_year,
                    fiscal_period,
                    {
                        "operating_cash_flow": cash_values.get("operating_cash_flow"),
                        "capex": cash_values.get("capex"),
                        "free_cash_flow": free_cash_flow,
                    },
                    company.id,
                )
                self.db.add(
                    CashFlowStatement(
                        company_id=company.id,
                        fiscal_year=fiscal_year,
                        fiscal_period=fiscal_period,
                        period_type="annual" if fiscal_period == "FY" else "quarterly",
                        currency="USD",
                        source_form=form,
                        source_accession_number=accession,
                        operating_cash_flow=operating_cash_flow,
                        capex=capex,
                        free_cash_flow=free_cash_flow,
                        net_income=Decimal("0"),
                        depreciation_and_amortization=Decimal("0"),
                        change_in_working_capital=Decimal("0"),
                        cash_from_operations=operating_cash_flow,
                        cash_from_investing=Decimal("0"),
                        debt_issued=Decimal("0"),
                        debt_repaid=Decimal("0"),
                        dividends_paid=Decimal("0"),
                        cash_from_financing=Decimal("0"),
                        net_change_in_cash=free_cash_flow,
                        ending_cash=Decimal("0"),
                    )
                )
                synced_cash_flow += 1
            else:
                self.validator.log_warning(
                    normalized_ticker,
                    "duplicate_period",
                    f"Skipped duplicate cash flow statement for {fiscal_year}-{fiscal_period}.",
                    company.id,
                )

        self.db.commit()

        return {
            "ticker": normalized_ticker,
            "cik": cik,
            "company_id": company.id,
            "synced_income_statements": synced_income,
            "synced_balance_sheets": synced_balance,
            "synced_cash_flow_statements": synced_cash_flow,
            "warnings_logged": self.validator.warning_count,
        }

    def _extract_periods(self, submissions: dict[str, Any], max_periods: int) -> list[dict[str, Any]]:
        recent = submissions.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        fiscal_years = recent.get("fy", [])
        fiscal_periods = recent.get("fp", [])
        accessions = recent.get("accessionNumber", [])

        periods: list[dict[str, Any]] = []
        for i, form in enumerate(forms):
            if form not in {"10-K", "10-Q"}:
                continue
            fy = fiscal_years[i]
            fp = fiscal_periods[i]
            if fy is None or fp is None:
                continue
            periods.append(
                {
                    "fiscal_year": int(fy),
                    "fiscal_period": str(fp),
                    "form": form,
                    "accession_number": accessions[i],
                }
            )
            if len(periods) >= max_periods:
                break
        return periods

    def _extract_period_values(
        self,
        company_facts: dict[str, Any],
        fiscal_year: int,
        fiscal_period: str,
        form: str,
        accession_number: str,
    ) -> dict[str, dict[str, Decimal | None]]:
        facts = company_facts.get("facts", {}).get("us-gaap", {})

        extracted: dict[str, dict[str, Decimal | None]] = {}
        for statement_name, metric_map in CANONICAL_TAG_MAPPINGS.items():
            values: dict[str, Decimal | None] = {}
            for canonical_metric, tags in metric_map.items():
                if canonical_metric == "free_cash_flow":
                    values[canonical_metric] = None
                    continue

                value = self._select_fact_value(
                    facts=facts,
                    tags=tags,
                    fiscal_year=fiscal_year,
                    fiscal_period=fiscal_period,
                    form=form,
                    accession_number=accession_number,
                    metric=canonical_metric,
                )
                values[canonical_metric] = value

            if statement_name == "cash_flow_statement":
                ocf = values.get("operating_cash_flow")
                capex = values.get("capex")
                if ocf is not None and capex is not None:
                    values["free_cash_flow"] = ocf - capex

            extracted[statement_name] = values

        return extracted

    def _select_fact_value(
        self,
        facts: dict[str, Any],
        tags: list[str],
        fiscal_year: int,
        fiscal_period: str,
        form: str,
        accession_number: str,
        metric: str,
    ) -> Decimal | None:
        for tag in tags:
            tag_data = facts.get(tag)
            if not tag_data:
                continue

            units = tag_data.get("units", {})
            candidate_units = ["USD"] if metric in USD_UNIT_METRICS else ["USD/shares", "shares"]
            for unit in candidate_units:
                rows = units.get(unit, [])
                if not rows:
                    continue

                frame = pd.DataFrame(rows)
                if frame.empty:
                    continue
                filtered = frame[
                    (frame.get("fy") == fiscal_year)
                    & (frame.get("fp") == fiscal_period)
                    & (frame.get("form") == form)
                    & (frame.get("accn") == accession_number)
                ]
                if filtered.empty:
                    filtered = frame[(frame.get("fy") == fiscal_year) & (frame.get("fp") == fiscal_period)]
                if filtered.empty:
                    continue

                val = filtered.iloc[-1].get("val")
                if val is None:
                    continue
                return Decimal(str(val))
        return None

    def _upsert_company(self, ticker: str, cik: int, submissions: dict[str, Any]) -> Company:
        company = self.get_company(ticker)
        company_name = submissions.get("name") or submissions.get("entityName") or ticker

        if company is None:
            company = Company(
                ticker=ticker,
                company_name=company_name,
                name=company_name,
                cik=cik,
                currency="USD",
                fiscal_year_end_month=12,
            )
            self.db.add(company)
            self.db.flush()
            return company

        company.cik = cik
        company.company_name = company_name
        company.name = company_name
        self.db.flush()
        return company
