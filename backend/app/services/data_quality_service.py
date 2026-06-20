from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.mappings.sec_xbrl_mappings import CANONICAL_TAG_MAPPINGS
from app.models.company import Company
from app.models.filing import Filing
from app.models.financial_value_trace import FinancialValueTrace
from app.models.mapping_exception import MappingException
from app.models.validation_issue import ValidationIssue


class DataQualityService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_quality(self, ticker: str) -> dict[str, object] | None:
        company = self.db.query(Company).filter(Company.ticker == ticker.upper()).one_or_none()
        if company is None:
            return None

        filing = (
            self.db.query(Filing)
            .filter(Filing.company_id == company.id)
            .order_by(Filing.fiscal_year.desc(), Filing.fiscal_period.desc(), Filing.filing_date.desc())
            .first()
        )
        if filing is None:
            return {
                "quality_score": 0,
                "warnings": ["No filings available"],
                "errors": ["No filings available"],
            }

        missing_fields = self._count_missing_fields(company.id, filing.id)
        missing_years, missing_quarters = self._missing_period_penalties(company.id)
        unmapped_tags = (
            self.db.query(func.count(MappingException.id))
            .filter(MappingException.company_id == company.id, MappingException.filing_id == filing.id)
            .scalar()
            or 0
        )
        failed_calculations = (
            self.db.query(func.count(ValidationIssue.id))
            .filter(
                ValidationIssue.company_id == company.id,
                ValidationIssue.filing_id == filing.id,
                ValidationIssue.severity == "error",
            )
            .scalar()
            or 0
        )

        score = Decimal("100")
        score -= Decimal(missing_fields * 3)
        score -= Decimal(missing_years * 5)
        score -= Decimal(missing_quarters * 2)
        score -= Decimal(unmapped_tags * 2)
        score -= Decimal(failed_calculations * 5)
        score = max(Decimal("0"), min(Decimal("100"), score))

        warning_rows = (
            self.db.query(ValidationIssue)
            .filter(
                ValidationIssue.company_id == company.id,
                ValidationIssue.filing_id == filing.id,
                ValidationIssue.severity == "warning",
            )
            .order_by(ValidationIssue.created_at.desc())
            .all()
        )
        error_rows = (
            self.db.query(ValidationIssue)
            .filter(
                ValidationIssue.company_id == company.id,
                ValidationIssue.filing_id == filing.id,
                ValidationIssue.severity == "error",
            )
            .order_by(ValidationIssue.created_at.desc())
            .all()
        )

        return {
            "quality_score": int(score),
            "warnings": [row.description for row in warning_rows],
            "errors": [row.description for row in error_rows],
        }

    def get_issues(self, ticker: str) -> dict[str, object] | None:
        company = self.db.query(Company).filter(Company.ticker == ticker.upper()).one_or_none()
        if company is None:
            return None

        validation_rows = (
            self.db.query(ValidationIssue)
            .filter(ValidationIssue.company_id == company.id)
            .order_by(ValidationIssue.created_at.desc())
            .all()
        )
        mapping_rows = (
            self.db.query(MappingException)
            .filter(MappingException.company_id == company.id)
            .order_by(MappingException.created_at.desc())
            .all()
        )

        return {
            "validation_issues": [
                {
                    "id": row.id,
                    "severity": row.severity,
                    "rule_name": row.rule_name,
                    "description": row.description,
                    "filing_id": row.filing_id,
                    "created_at": row.created_at,
                }
                for row in validation_rows
            ],
            "mapping_exceptions": [
                {
                    "id": row.id,
                    "xbrl_tag": row.xbrl_tag,
                    "attempted_field": row.attempted_field,
                    "confidence": float(row.confidence) if row.confidence is not None else None,
                    "notes": row.notes,
                    "filing_id": row.filing_id,
                    "created_at": row.created_at,
                }
                for row in mapping_rows
            ],
        }

    def _count_missing_fields(self, company_id: int, filing_id: int) -> int:
        expected_fields = sum(len(fields) for fields in CANONICAL_TAG_MAPPINGS.values())
        present_fields = (
            self.db.query(func.count(FinancialValueTrace.id))
            .filter(
                FinancialValueTrace.company_id == company_id,
                FinancialValueTrace.filing_id == filing_id,
                FinancialValueTrace.value_numeric.is_not(None),
            )
            .scalar()
            or 0
        )
        return max(expected_fields - present_fields, 0)

    def _missing_period_penalties(self, company_id: int) -> tuple[int, int]:
        filings = (
            self.db.query(Filing)
            .filter(Filing.company_id == company_id)
            .order_by(Filing.fiscal_year.desc(), Filing.fiscal_period.asc())
            .all()
        )
        if not filings:
            return 1, 4

        years = sorted({filing.fiscal_year for filing in filings})
        min_year = years[0]
        max_year = years[-1]
        expected_years = set(range(min_year, max_year + 1))
        missing_years = len(expected_years - set(years))

        latest_year = max_year
        latest_quarters = {filing.fiscal_period for filing in filings if filing.fiscal_year == latest_year and filing.fiscal_period.startswith("Q")}
        missing_quarters = max(4 - len(latest_quarters), 0)
        return missing_years, missing_quarters
