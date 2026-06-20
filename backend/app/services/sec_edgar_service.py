from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.base import PeriodType
from app.schemas.balance_sheet import BalanceSheetCreate
from app.schemas.cash_flow_statement import CashFlowStatementCreate
from app.schemas.company import CompanyCreate
from app.schemas.income_statement import IncomeStatementCreate
from app.services.company_service import CompanyService
from app.services.statement_service import BalanceSheetService, CashFlowStatementService, IncomeStatementService

settings = get_settings()


SEC_BASE_URL = "https://www.sec.gov"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/"
SEC_TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"


INCOME_TAG_MAP: dict[str, tuple[str, str]] = {
    "RevenueFromContractWithCustomerExcludingAssessedTax": ("revenue", "instant"),
    "SalesRevenueNet": ("revenue", "instant"),
    "Revenues": ("revenue", "instant"),
    "CostOfGoodsSold": ("cogs", "instant"),
    "CostOfRevenue": ("cogs", "instant"),
    "GrossProfit": ("gross_profit", "instant"),
    "OperatingExpenses": ("operating_expenses", "instant"),
    "OperatingIncomeLoss": ("operating_income", "instant"),
    "DepreciationDepletionAndAmortization": ("depreciation_and_amortization", "instant"),
    "DepreciationAmortizationAndAccretionNet": ("depreciation_and_amortization", "instant"),
    "InterestExpenseAndOther": ("interest_expense", "instant"),
    "InterestExpense": ("interest_expense", "instant"),
    "IncomeBeforeTaxExpenseBenefit": ("pretax_income", "instant"),
    "IncomeBeforeTaxExpenseBenefit": ("pretax_income", "instant"),
    "IncomeTaxExpenseBenefit": ("tax_expense", "instant"),
    "NetIncomeLoss": ("net_income", "instant"),
}

BALANCE_TAG_MAP: dict[str, tuple[str, str]] = {
    "CashAndCashEquivalentsAtCarryingValue": ("cash_and_equivalents", "instant"),
    "AccountsReceivableNetCurrent": ("accounts_receivable", "instant"),
    "InventoryNet": ("inventory", "instant"),
    "AssetsCurrent": ("total_current_assets", "instant"),
    "PropertyPlantAndEquipmentNet": ("property_plant_equipment", "instant"),
    "Assets": ("total_assets", "instant"),
    "AccountsPayableCurrent": ("accounts_payable", "instant"),
    "ShortTermBorrowings": ("short_term_debt", "instant"),
    "LiabilitiesCurrent": ("total_current_liabilities", "instant"),
    "LongTermDebtCurrent": ("long_term_debt", "instant"),
    "LongTermDebtAndFinanceLeaseObligations": ("long_term_debt", "instant"),
    "Liabilities": ("total_liabilities", "instant"),
    "StockholdersEquity": ("total_equity", "instant"),
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": ("total_equity", "instant"),
}

CASH_FLOW_TAG_MAP: dict[str, tuple[str, str]] = {
    "NetIncomeLoss": ("net_income", "instant"),
    "DepreciationDepletionAndAmortization": ("depreciation_and_amortization", "instant"),
    "NetCashProvidedByUsedInOperatingActivities": ("cash_from_operations", "instant"),
    "PaymentsToAcquirePropertyPlantAndEquipment": ("capex", "instant"),
    "NetCashProvidedByUsedInInvestingActivities": ("cash_from_investing", "instant"),
    "ProceedsFromIssuanceOfLongTermDebt": ("debt_issued", "instant"),
    "RepaymentsOfLongTermDebt": ("debt_repaid", "instant"),
    "PaymentsOfDividends": ("dividends_paid", "instant"),
    "NetCashProvidedByUsedInFinancingActivities": ("cash_from_financing", "instant"),
    "CashAndCashEquivalentsPeriodIncreaseDecrease": ("net_change_in_cash", "instant"),
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents": ("ending_cash", "instant"),
}


@dataclass(slots=True)
class FilingBundle:
    accession_number: str
    filing_date: date
    form_type: str
    frames: dict[str, pd.DataFrame]


class SECIngestionError(RuntimeError):
    pass


class SecEdgarService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.company_service = CompanyService(db)
        self.income_service = IncomeStatementService(db)
        self.balance_service = BalanceSheetService(db)
        self.cash_flow_service = CashFlowStatementService(db)

    def ingest_ticker(self, ticker: str, filing_count: int = 1) -> dict[str, Any]:
        normalized_ticker = ticker.upper().strip()
        cik = self.resolve_cik(normalized_ticker)
        company_meta = self.fetch_company_metadata(cik)
        company = self.upsert_company(normalized_ticker, cik, company_meta)
        filings = self.fetch_recent_filings(cik, filing_count=filing_count)

        saved_records: list[dict[str, Any]] = []
        for filing in filings:
            bundles = self.fetch_xbrl_bundle(cik, filing["accessionNumber"], filing["primaryDocument"])
            saved_records.append(self.save_filing(company.id, filing, bundles))

        return {
            "ticker": normalized_ticker,
            "cik": cik,
            "company_id": company.id,
            "filings_processed": len(saved_records),
            "results": saved_records,
        }

    def resolve_cik(self, ticker: str) -> int:
        payload = self._get_json(SEC_TICKER_MAP_URL)
        for row in payload.values():
            if str(row["ticker"]).upper() == ticker:
                return int(row["cik_str"])
        raise SECIngestionError(f"Unable to resolve CIK for ticker {ticker}.")

    def fetch_company_metadata(self, cik: int) -> dict[str, Any]:
        submissions = self._get_json(urljoin(SEC_SUBMISSIONS_URL, f"CIK{cik:010d}.json"))
        company_name = submissions.get("name") or submissions.get("entityName")
        tickers = submissions.get("tickers") or []
        return {
            "name": company_name,
            "ticker": tickers[0] if tickers else None,
            "fiscal_year_end_month": int(str(submissions.get("fiscalYearEnd", "12"))[:2]),
            "currency": "USD",
            "sector": None,
            "industry": None,
            "country": submissions.get("addresses", {}).get("mailing", {}).get("country"),
        }

    def upsert_company(self, ticker: str, cik: int, metadata: dict[str, Any]):
        existing = self.company_service.get_by_ticker(ticker)
        if existing is None:
            payload = CompanyCreate(
                cik=cik,
                ticker=ticker,
                name=metadata.get("name") or ticker,
                sector=metadata.get("sector"),
                industry=metadata.get("industry"),
                country=metadata.get("country"),
                currency=metadata.get("currency") or "USD",
                fiscal_year_end_month=metadata.get("fiscal_year_end_month") or 12,
            )
            return self.company_service.create(payload)

        existing.cik = cik
        existing.name = metadata.get("name") or existing.name
        existing.country = metadata.get("country") or existing.country
        existing.currency = metadata.get("currency") or existing.currency
        self.db.commit()
        self.db.refresh(existing)
        return existing

    def fetch_recent_filings(self, cik: int, filing_count: int = 1) -> list[dict[str, Any]]:
        submissions = self._get_json(urljoin(SEC_SUBMISSIONS_URL, f"CIK{cik:010d}.json"))
        recent = submissions.get("filings", {}).get("recent", {})
        accession_numbers = recent.get("accessionNumber", [])
        primary_documents = recent.get("primaryDocument", [])
        form_types = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])

        filings: list[dict[str, Any]] = []
        for index, form in enumerate(form_types):
            if form not in {"10-K", "10-Q"}:
                continue
            filings.append(
                {
                    "accessionNumber": accession_numbers[index],
                    "primaryDocument": primary_documents[index],
                    "form": form,
                    "filingDate": date.fromisoformat(filing_dates[index]),
                }
            )
            if len(filings) >= filing_count:
                break

        if not filings:
            raise SECIngestionError(f"No recent 10-K or 10-Q filings found for CIK {cik}.")
        return filings

    def fetch_xbrl_bundle(self, cik: int, accession_number: str, primary_document: str) -> FilingBundle:
        accession_no_dashes = accession_number.replace("-", "")
        filing_directory = f"{SEC_BASE_URL}/Archives/edgar/data/{cik}/{accession_no_dashes}/"
        index = self._get_json(urljoin(filing_directory, "index.json"))
        frames: dict[str, pd.DataFrame] = {}

        for item in index.get("directory", {}).get("item", []):
            name = item.get("name", "")
            if not name.lower().endswith(".xml"):
                continue
            if not any(token in name.lower() for token in ("facts", "xml", "ins", "cal", "def")):
                continue
            xml_text = self._get_text(urljoin(filing_directory, name))
            try:
                frame = pd.read_xml(xml_text)
            except ValueError:
                continue
            if not frame.empty:
                frames[name] = frame

        if not frames:
            raise SECIngestionError(f"No readable XBRL XML documents found for accession {accession_number}.")

        return FilingBundle(
            accession_number=accession_number,
            filing_date=date.today(),
            form_type="10-K",
            frames=frames,
        )

    def save_filing(self, company_id: int, filing: dict[str, Any], bundle: FilingBundle) -> dict[str, Any]:
        facts = self.extract_standardized_facts(bundle.frames)

        income_payload = self.build_income_statement_payload(company_id, filing, facts)
        balance_payload = self.build_balance_sheet_payload(company_id, filing, facts)
        cash_flow_payload = self.build_cash_flow_payload(company_id, filing, facts)

        income = self.income_service.create(income_payload)
        balance = self.balance_service.create(balance_payload)
        cash_flow = self.cash_flow_service.create(cash_flow_payload)

        return {
            "accession_number": filing["accessionNumber"],
            "filing_date": filing["filingDate"].isoformat(),
            "form": filing["form"],
            "income_statement_id": income.id,
            "balance_sheet_id": balance.id,
            "cash_flow_statement_id": cash_flow.id,
        }

    def extract_standardized_facts(self, frames: dict[str, pd.DataFrame]) -> dict[str, Decimal]:
        facts: dict[str, Decimal] = {}
        for frame_name, frame in frames.items():
            lower_columns = {column.lower(): column for column in frame.columns}
            for tag_map in (INCOME_TAG_MAP, BALANCE_TAG_MAP, CASH_FLOW_TAG_MAP):
                for xbrl_tag, (field_name, _) in tag_map.items():
                    if xbrl_tag.lower() in lower_columns:
                        column_name = lower_columns[xbrl_tag.lower()]
                        series = frame[column_name].dropna()
                        if series.empty:
                            continue
                        value = self._coerce_decimal(series.iloc[-1])
                        if field_name not in facts or abs(value) > abs(facts[field_name]):
                            facts[field_name] = value
        return facts

    def build_income_statement_payload(self, company_id: int, filing: dict[str, Any], facts: dict[str, Decimal]) -> IncomeStatementCreate:
        revenue = facts.get("revenue", Decimal("0"))
        cogs = facts.get("cogs", Decimal("0"))
        gross_profit = facts.get("gross_profit", revenue - cogs)
        operating_expenses = facts.get("operating_expenses", Decimal("0"))
        ebitda = facts.get("ebitda", gross_profit - operating_expenses)
        depreciation_and_amortization = facts.get("depreciation_and_amortization", Decimal("0"))
        operating_income = facts.get("operating_income", ebitda - depreciation_and_amortization)
        interest_expense = facts.get("interest_expense", Decimal("0"))
        pretax_income = facts.get("pretax_income", operating_income - interest_expense)
        tax_expense = facts.get("tax_expense", Decimal("0"))
        net_income = facts.get("net_income", pretax_income - tax_expense)

        return IncomeStatementCreate(
            company_id=company_id,
            fiscal_year=filing["filingDate"].year,
            period_type=self._infer_period_type(filing["form"]),
            currency="USD",
            revenue=revenue,
            cogs=cogs,
            gross_profit=gross_profit,
            operating_expenses=operating_expenses,
            ebitda=ebitda,
            depreciation_and_amortization=depreciation_and_amortization,
            operating_income=operating_income,
            interest_expense=interest_expense,
            pretax_income=pretax_income,
            tax_expense=tax_expense,
            net_income=net_income,
            source_accession_number=filing["accessionNumber"],
            source_filing_date=filing["filingDate"],
            source_form=filing["form"],
        )

    def build_balance_sheet_payload(self, company_id: int, filing: dict[str, Any], facts: dict[str, Decimal]) -> BalanceSheetCreate:
        cash_and_equivalents = facts.get("cash_and_equivalents", Decimal("0"))
        accounts_receivable = facts.get("accounts_receivable", Decimal("0"))
        inventory = facts.get("inventory", Decimal("0"))
        total_current_assets = facts.get("total_current_assets", cash_and_equivalents + accounts_receivable + inventory)
        property_plant_equipment = facts.get("property_plant_equipment", Decimal("0"))
        total_assets = facts.get("total_assets", total_current_assets + property_plant_equipment)
        accounts_payable = facts.get("accounts_payable", Decimal("0"))
        short_term_debt = facts.get("short_term_debt", Decimal("0"))
        total_current_liabilities = facts.get("total_current_liabilities", accounts_payable + short_term_debt)
        long_term_debt = facts.get("long_term_debt", Decimal("0"))
        total_liabilities = facts.get("total_liabilities", total_current_liabilities + long_term_debt)
        total_equity = facts.get("total_equity", total_assets - total_liabilities)

        return BalanceSheetCreate(
            company_id=company_id,
            fiscal_year=filing["filingDate"].year,
            period_type=self._infer_period_type(filing["form"]),
            currency="USD",
            cash_and_equivalents=cash_and_equivalents,
            accounts_receivable=accounts_receivable,
            inventory=inventory,
            total_current_assets=total_current_assets,
            property_plant_equipment=property_plant_equipment,
            total_assets=total_assets,
            accounts_payable=accounts_payable,
            short_term_debt=short_term_debt,
            total_current_liabilities=total_current_liabilities,
            long_term_debt=long_term_debt,
            total_liabilities=total_liabilities,
            total_equity=total_equity,
            source_accession_number=filing["accessionNumber"],
            source_filing_date=filing["filingDate"],
            source_form=filing["form"],
        )

    def build_cash_flow_payload(self, company_id: int, filing: dict[str, Any], facts: dict[str, Decimal]) -> CashFlowStatementCreate:
        net_income = facts.get("net_income", Decimal("0"))
        depreciation_and_amortization = facts.get("depreciation_and_amortization", Decimal("0"))
        cash_from_operations = facts.get("cash_from_operations", net_income + depreciation_and_amortization)
        capex = facts.get("capex", Decimal("0"))
        cash_from_investing = facts.get("cash_from_investing", Decimal("0"))
        debt_issued = facts.get("debt_issued", Decimal("0"))
        debt_repaid = facts.get("debt_repaid", Decimal("0"))
        dividends_paid = facts.get("dividends_paid", Decimal("0"))
        cash_from_financing = facts.get("cash_from_financing", debt_issued - debt_repaid - dividends_paid)
        net_change_in_cash = facts.get("net_change_in_cash", cash_from_operations + cash_from_investing + cash_from_financing)
        ending_cash = facts.get("ending_cash", net_change_in_cash)

        return CashFlowStatementCreate(
            company_id=company_id,
            fiscal_year=filing["filingDate"].year,
            period_type=self._infer_period_type(filing["form"]),
            currency="USD",
            net_income=net_income,
            depreciation_and_amortization=depreciation_and_amortization,
            change_in_working_capital=facts.get("change_in_working_capital", Decimal("0")),
            cash_from_operations=cash_from_operations,
            capex=capex,
            cash_from_investing=cash_from_investing,
            debt_issued=debt_issued,
            debt_repaid=debt_repaid,
            dividends_paid=dividends_paid,
            cash_from_financing=cash_from_financing,
            net_change_in_cash=net_change_in_cash,
            ending_cash=ending_cash,
            source_accession_number=filing["accessionNumber"],
            source_filing_date=filing["filingDate"],
            source_form=filing["form"],
        )

    def _infer_period_type(self, form: str) -> PeriodType:
        return PeriodType.annual if form == "10-K" else PeriodType.quarterly

    def _coerce_decimal(self, value: Any) -> Decimal:
        if value is None:
            return Decimal("0")
        if isinstance(value, Decimal):
            return value
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        text = str(value).strip()
        if not text:
            return Decimal("0")
        cleaned = re.sub(r"[^0-9\-\.]+", "", text)
        if cleaned in {"", "-", ".", "-."}:
            return Decimal("0")
        return Decimal(cleaned)

    def _get_json(self, url: str) -> dict[str, Any]:
        response_text = self._request(url)
        return json.loads(response_text)

    def _get_text(self, url: str) -> str:
        return self._request(url)

    def _request(self, url: str) -> str:
        request = Request(url, headers={"User-Agent": settings.sec_user_agent, "Accept-Encoding": "gzip, deflate"})
        try:
            with urlopen(request, timeout=settings.sec_request_timeout_seconds) as response:
                payload = response.read()
                return payload.decode("utf-8", errors="replace")
        except (HTTPError, URLError) as exc:
            raise SECIngestionError(f"SEC request failed for {url}: {exc}") from exc

