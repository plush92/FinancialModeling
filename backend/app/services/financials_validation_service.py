from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import json

from sqlalchemy.orm import Session

from app.models.balance_sheet import BalanceSheet
from app.models.cash_flow_statement import CashFlowStatement
from app.models.ingestion_exception import IngestionException
from app.models.income_statement import IncomeStatement


class FinancialsValidationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.warning_count = 0

    def log_warning(self, ticker: str, category: str, message: str, company_id: int | None = None, context: str | None = None) -> None:
        self.warning_count += 1
        serialized_context = self._serialize_context(context)
        self.db.add(
            IngestionException(
                ticker=ticker,
                company_id=company_id,
                level="warning",
                category=category,
                message=message,
                context=serialized_context,
            )
        )

    def log_error(
        self,
        ticker: str,
        category: str,
        message: str,
        company_id: int | None = None,
        context: dict[str, object] | str | None = None,
    ) -> None:
        serialized_context = self._serialize_context(context)
        self.db.add(
            IngestionException(
                ticker=ticker,
                company_id=company_id,
                level="error",
                category=category,
                message=message,
                context=serialized_context,
            )
        )

    def validate_fiscal_year(self, ticker: str, fiscal_year: int, company_id: int | None = None) -> bool:
        current_year = datetime.utcnow().year + 1
        if fiscal_year < 1990 or fiscal_year > current_year:
            self.log_warning(
                ticker=ticker,
                category="invalid_fiscal_year",
                message=f"Fiscal year {fiscal_year} is outside expected range.",
                company_id=company_id,
            )
            return False
        return True

    def validate_required_values(
        self,
        ticker: str,
        statement_type: str,
        fiscal_year: int,
        fiscal_period: str,
        required_values: dict[str, Decimal | None],
        company_id: int | None = None,
    ) -> None:
        missing_fields = [field for field, value in required_values.items() if value is None]
        if missing_fields:
            self.log_warning(
                ticker=ticker,
                category="missing_values",
                message=f"Missing values in {statement_type} for {fiscal_year}-{fiscal_period}: {', '.join(missing_fields)}",
                company_id=company_id,
            )

    def _serialize_context(self, context: dict[str, object] | str | None) -> str | None:
        if context is None:
            return None
        if isinstance(context, str):
            return context
        return json.dumps(context, default=str)

    def is_duplicate_period(self, model: type, company_id: int, fiscal_year: int, fiscal_period: str) -> bool:
        return (
            self.db.query(model)
            .filter(
                model.company_id == company_id,
                model.fiscal_year == fiscal_year,
                model.fiscal_period == fiscal_period,
            )
            .first()
            is not None
        )

    def validate_balance_sheet_equation(
        self,
        ticker: str,
        fiscal_year: int,
        fiscal_period: str,
        total_assets: Decimal,
        total_liabilities: Decimal,
        shareholder_equity: Decimal,
        company_id: int | None = None,
    ) -> None:
        lhs = total_assets.quantize(Decimal("0.01"))
        rhs = (total_liabilities + shareholder_equity).quantize(Decimal("0.01"))
        if abs(lhs - rhs) > Decimal("1.00"):
            self.log_warning(
                ticker=ticker,
                category="reconciliation_mismatch",
                message=(
                    f"Assets != Liabilities + Equity for {fiscal_year}-{fiscal_period}. "
                    f"Assets={lhs}, Liabilities+Equity={rhs}"
                ),
                company_id=company_id,
            )

