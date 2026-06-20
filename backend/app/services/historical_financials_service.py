from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.mappings.sec_xbrl_mappings import CANONICAL_TAG_MAPPINGS, USD_UNIT_METRICS
from app.models.balance_sheet import BalanceSheet
from app.models.base import PeriodType
from app.models.cash_flow_statement import CashFlowStatement
from app.models.company import Company
from app.models.income_statement import IncomeStatement
from app.services.financials_validation_service import FinancialsValidationService
from app.services.sec_client import SECClient, SECClientError


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
        try:
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
                filing_date = period.get("filing_date")

                if not self.validator.validate_fiscal_year(normalized_ticker, fiscal_year, company.id):
                    continue

                extracted = self._extract_period_values(facts, fiscal_year, fiscal_period, form, accession)

                synced_income += self._upsert_income_statement(
                    ticker=normalized_ticker,
                    company=company,
                    fiscal_year=fiscal_year,
                    fiscal_period=fiscal_period,
                    form=form,
                    accession=accession,
                    filing_date=filing_date,
                    values=extracted["income_statement"],
                )
                synced_balance += self._upsert_balance_sheet(
                    ticker=normalized_ticker,
                    company=company,
                    fiscal_year=fiscal_year,
                    fiscal_period=fiscal_period,
                    form=form,
                    accession=accession,
                    filing_date=filing_date,
                    values=extracted["balance_sheet"],
                )
                synced_cash_flow += self._upsert_cash_flow_statement(
                    ticker=normalized_ticker,
                    company=company,
                    fiscal_year=fiscal_year,
                    fiscal_period=fiscal_period,
                    form=form,
                    accession=accession,
                    filing_date=filing_date,
                    values=extracted["cash_flow_statement"],
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
        except (SECClientError, SQLAlchemyError, ValueError) as exc:
            self.db.rollback()
            self.validator.log_error(
                ticker=normalized_ticker,
                category="sync_failure",
                message=str(exc),
                context={"max_periods": max_periods},
            )
            self.db.commit()
            raise

    def _extract_periods(self, submissions: dict[str, Any], max_periods: int) -> list[dict[str, Any]]:
        recent = submissions.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        fiscal_years = recent.get("fy", [])
        fiscal_periods = recent.get("fp", [])
        accessions = recent.get("accessionNumber", [])
        filing_dates = recent.get("filingDate", [])

        periods: list[dict[str, Any]] = []
        seen_keys: set[tuple[int, str]] = set()
        for i, form in enumerate(forms):
            if form not in {"10-K", "10-Q"}:
                continue
            fy = fiscal_years[i]
            fp = fiscal_periods[i]
            if fy is None or fp is None:
                continue
            fiscal_period = self._normalize_fiscal_period(str(fp), form)
            period_key = (int(fy), fiscal_period)
            if period_key in seen_keys:
                continue
            seen_keys.add(period_key)
            periods.append(
                {
                    "fiscal_year": int(fy),
                    "fiscal_period": fiscal_period,
                    "form": form,
                    "accession_number": accessions[i],
                    "filing_date": self._parse_filing_date(filing_dates[i] if i < len(filing_dates) else None),
                }
            )
            if len(periods) >= max_periods:
                break
        return periods

    def _parse_filing_date(self, raw_value: Any) -> date | None:
        if raw_value is None:
            return None
        text = str(raw_value).strip()
        if not text:
            return None
        try:
            return date.fromisoformat(text)
        except ValueError:
            return None

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
                    values["free_cash_flow"] = ocf - abs(capex)

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
        if metric == "total_debt":
            return self._select_total_debt_value(
                facts=facts,
                tags=tags,
                fiscal_year=fiscal_year,
                fiscal_period=fiscal_period,
                form=form,
                accession_number=accession_number,
            )

        for tag in tags:
            value = self._select_tag_value(
                facts=facts,
                tag=tag,
                fiscal_year=fiscal_year,
                fiscal_period=fiscal_period,
                form=form,
                accession_number=accession_number,
                metric=metric,
            )
            if value is not None:
                return value
        return None

    def _select_total_debt_value(
        self,
        facts: dict[str, Any],
        tags: list[str],
        fiscal_year: int,
        fiscal_period: str,
        form: str,
        accession_number: str,
    ) -> Decimal | None:
        primary_total = self._select_tag_value(
            facts=facts,
            tag="LongTermDebtAndFinanceLeaseObligations",
            fiscal_year=fiscal_year,
            fiscal_period=fiscal_period,
            form=form,
            accession_number=accession_number,
            metric="total_debt",
        )
        if primary_total is not None:
            return abs(primary_total)

        debt_components: list[Decimal] = []
        for component_tag in ("LongTermDebtCurrent", "ShortTermBorrowings"):
            value = self._select_tag_value(
                facts=facts,
                tag=component_tag,
                fiscal_year=fiscal_year,
                fiscal_period=fiscal_period,
                form=form,
                accession_number=accession_number,
                metric="total_debt",
            )
            if value is not None:
                debt_components.append(abs(value))
        if debt_components:
            return sum(debt_components, start=Decimal("0"))

        for fallback_tag in tags:
            fallback = self._select_tag_value(
                facts=facts,
                tag=fallback_tag,
                fiscal_year=fiscal_year,
                fiscal_period=fiscal_period,
                form=form,
                accession_number=accession_number,
                metric="total_debt",
            )
            if fallback is not None:
                return abs(fallback)
        return None

    def _select_tag_value(
        self,
        facts: dict[str, Any],
        tag: str,
        fiscal_year: int,
        fiscal_period: str,
        form: str,
        accession_number: str,
        metric: str,
    ) -> Decimal | None:
        tag_data = facts.get(tag)
        if not tag_data:
            return None

        units = tag_data.get("units", {})
        candidate_units = ["USD"] if metric in USD_UNIT_METRICS else ["USD/shares", "shares"]
        for unit in candidate_units:
            rows = units.get(unit, [])
            if not rows:
                continue

            exact = self._pick_row(rows, fiscal_year, fiscal_period, form, accession_number, strict=True)
            if exact is None:
                exact = self._pick_row(rows, fiscal_year, fiscal_period, form, accession_number, strict=False)
            if exact is None:
                continue

            raw_value = exact.get("val")
            if raw_value is None:
                continue
            value = Decimal(str(raw_value))
            if metric == "capex":
                return abs(value)
            return value
        return None

    def _pick_row(
        self,
        rows: Iterable[dict[str, Any]],
        fiscal_year: int,
        fiscal_period: str,
        form: str,
        accession_number: str,
        strict: bool,
    ) -> dict[str, Any] | None:
        matches: list[dict[str, Any]] = []
        for row in rows:
            if row.get("fy") != fiscal_year or row.get("fp") != fiscal_period:
                continue
            if strict and (row.get("form") != form or row.get("accn") != accession_number):
                continue
            matches.append(row)

        if not matches:
            return None

        # Prefer the latest filing date/end date when multiple facts exist for a period.
        matches.sort(key=lambda item: (str(item.get("filed", "")), str(item.get("end", ""))))
        return matches[-1]

    def _normalize_fiscal_period(self, raw_period: str, form: str) -> str:
        normalized = raw_period.upper().strip()
        if normalized == "FY":
            return "FY"
        if normalized in {"Q1", "Q2", "Q3", "Q4"}:
            return normalized
        if form == "10-K":
            return "FY"
        if normalized in {"H1", "H2"}:
            return "Q2" if normalized == "H1" else "Q4"
        return "Q4" if form == "10-K" else "Q1"

    def _period_type_from_fiscal_period(self, fiscal_period: str) -> PeriodType:
        return PeriodType.annual if fiscal_period == "FY" else PeriodType.quarterly

    def _upsert_income_statement(
        self,
        ticker: str,
        company: Company,
        fiscal_year: int,
        fiscal_period: str,
        form: str,
        accession: str,
        filing_date: date | None,
        values: dict[str, Decimal | None],
    ) -> int:
        revenue = values.get("revenue")
        gross_profit = values.get("gross_profit")
        operating_income = values.get("operating_income")
        net_income = values.get("net_income")
        eps = values.get("eps")

        self.validator.validate_required_values(
            ticker,
            "income_statement",
            fiscal_year,
            fiscal_period,
            {
                "revenue": revenue,
                "gross_profit": gross_profit,
                "operating_income": operating_income,
                "net_income": net_income,
                "eps": eps,
            },
            company.id,
        )

        existing = (
            self.db.query(IncomeStatement)
            .filter(
                IncomeStatement.company_id == company.id,
                IncomeStatement.fiscal_year == fiscal_year,
                IncomeStatement.fiscal_period == fiscal_period,
            )
            .one_or_none()
        )

        payload = {
            "company_id": company.id,
            "fiscal_year": fiscal_year,
            "fiscal_period": fiscal_period,
            "period_type": self._period_type_from_fiscal_period(fiscal_period),
            "currency": "USD",
            "source_form": form,
            "source_accession_number": accession,
            "source_filing_date": filing_date,
            "revenue": revenue or Decimal("0"),
            "cogs": Decimal("0"),
            "gross_profit": gross_profit or Decimal("0"),
            "operating_expenses": Decimal("0"),
            "ebitda": operating_income or Decimal("0"),
            "depreciation_and_amortization": Decimal("0"),
            "operating_income": operating_income or Decimal("0"),
            "interest_expense": Decimal("0"),
            "pretax_income": net_income or Decimal("0"),
            "tax_expense": Decimal("0"),
            "net_income": net_income or Decimal("0"),
            "eps": eps or Decimal("0"),
        }

        if existing is None:
            self.db.add(IncomeStatement(**payload))
            return 1

        for key, value in payload.items():
            setattr(existing, key, value)
        return 0

    def _upsert_balance_sheet(
        self,
        ticker: str,
        company: Company,
        fiscal_year: int,
        fiscal_period: str,
        form: str,
        accession: str,
        filing_date: date | None,
        values: dict[str, Decimal | None],
    ) -> int:
        cash = values.get("cash")
        total_assets = values.get("total_assets")
        total_liabilities = values.get("total_liabilities")
        shareholder_equity = values.get("shareholder_equity")
        total_debt = values.get("total_debt")

        self.validator.validate_required_values(
            ticker,
            "balance_sheet",
            fiscal_year,
            fiscal_period,
            {
                "cash": cash,
                "total_assets": total_assets,
                "total_liabilities": total_liabilities,
                "shareholder_equity": shareholder_equity,
                "total_debt": total_debt,
            },
            company.id,
        )

        assets_value = total_assets or Decimal("0")
        liabilities_value = total_liabilities or Decimal("0")
        equity_value = shareholder_equity or Decimal("0")
        self.validator.validate_balance_sheet_equation(
            ticker,
            fiscal_year,
            fiscal_period,
            assets_value,
            liabilities_value,
            equity_value,
            company.id,
        )

        existing = (
            self.db.query(BalanceSheet)
            .filter(
                BalanceSheet.company_id == company.id,
                BalanceSheet.fiscal_year == fiscal_year,
                BalanceSheet.fiscal_period == fiscal_period,
            )
            .one_or_none()
        )

        payload = {
            "company_id": company.id,
            "fiscal_year": fiscal_year,
            "fiscal_period": fiscal_period,
            "period_type": self._period_type_from_fiscal_period(fiscal_period),
            "currency": "USD",
            "source_form": form,
            "source_accession_number": accession,
            "source_filing_date": filing_date,
            "cash": cash or Decimal("0"),
            "total_assets": assets_value,
            "total_liabilities": liabilities_value,
            "shareholder_equity": equity_value,
            "total_debt": total_debt or Decimal("0"),
            "cash_and_equivalents": cash or Decimal("0"),
            "accounts_receivable": Decimal("0"),
            "inventory": Decimal("0"),
            "total_current_assets": cash or Decimal("0"),
            "property_plant_equipment": Decimal("0"),
            "accounts_payable": Decimal("0"),
            "short_term_debt": Decimal("0"),
            "total_current_liabilities": Decimal("0"),
            "long_term_debt": total_debt or Decimal("0"),
            "total_equity": equity_value,
        }

        if existing is None:
            self.db.add(BalanceSheet(**payload))
            return 1

        for key, value in payload.items():
            setattr(existing, key, value)
        return 0

    def _upsert_cash_flow_statement(
        self,
        ticker: str,
        company: Company,
        fiscal_year: int,
        fiscal_period: str,
        form: str,
        accession: str,
        filing_date: date | None,
        values: dict[str, Decimal | None],
    ) -> int:
        operating_cash_flow = values.get("operating_cash_flow")
        capex = values.get("capex")
        free_cash_flow = values.get("free_cash_flow")
        if free_cash_flow is None and operating_cash_flow is not None and capex is not None:
            free_cash_flow = operating_cash_flow - abs(capex)

        self.validator.validate_required_values(
            ticker,
            "cash_flow_statement",
            fiscal_year,
            fiscal_period,
            {
                "operating_cash_flow": operating_cash_flow,
                "capex": capex,
                "free_cash_flow": free_cash_flow,
            },
            company.id,
        )

        existing = (
            self.db.query(CashFlowStatement)
            .filter(
                CashFlowStatement.company_id == company.id,
                CashFlowStatement.fiscal_year == fiscal_year,
                CashFlowStatement.fiscal_period == fiscal_period,
            )
            .one_or_none()
        )

        payload = {
            "company_id": company.id,
            "fiscal_year": fiscal_year,
            "fiscal_period": fiscal_period,
            "period_type": self._period_type_from_fiscal_period(fiscal_period),
            "currency": "USD",
            "source_form": form,
            "source_accession_number": accession,
            "source_filing_date": filing_date,
            "operating_cash_flow": operating_cash_flow or Decimal("0"),
            "capex": abs(capex) if capex is not None else Decimal("0"),
            "free_cash_flow": free_cash_flow or Decimal("0"),
            "net_income": Decimal("0"),
            "depreciation_and_amortization": Decimal("0"),
            "change_in_working_capital": Decimal("0"),
            "cash_from_operations": operating_cash_flow or Decimal("0"),
            "cash_from_investing": Decimal("0"),
            "debt_issued": Decimal("0"),
            "debt_repaid": Decimal("0"),
            "dividends_paid": Decimal("0"),
            "cash_from_financing": Decimal("0"),
            "net_change_in_cash": free_cash_flow or Decimal("0"),
            "ending_cash": Decimal("0"),
        }

        if existing is None:
            self.db.add(CashFlowStatement(**payload))
            return 1

        for key, value in payload.items():
            setattr(existing, key, value)
        return 0

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
