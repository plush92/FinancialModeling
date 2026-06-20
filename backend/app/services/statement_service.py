from decimal import Decimal

import pandas as pd

from app.models.base import PeriodType
from app.models.balance_sheet import BalanceSheet
from app.models.cash_flow_statement import CashFlowStatement
from app.models.income_statement import IncomeStatement
from app.schemas.balance_sheet import BalanceSheetCreate, BalanceSheetUpdate
from app.schemas.cash_flow_statement import CashFlowStatementCreate, CashFlowStatementUpdate
from app.schemas.income_statement import IncomeStatementCreate, IncomeStatementUpdate
from app.services.base import CRUDService


class StatementServiceBase(CRUDService):
    def list_by_company(self, company_id: int, skip: int = 0, limit: int = 100):
        return (
            self.db.query(self.model)
            .filter(self.model.company_id == company_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_for_period(self, company_id: int, fiscal_year: int, period_type: PeriodType):
        return (
            self.db.query(self.model)
            .filter(
                self.model.company_id == company_id,
                self.model.fiscal_year == fiscal_year,
                self.model.period_type == period_type,
            )
            .one_or_none()
        )


class IncomeStatementService(StatementServiceBase[IncomeStatement, IncomeStatementCreate, IncomeStatementUpdate]):
    model = IncomeStatement


class BalanceSheetService(StatementServiceBase[BalanceSheet, BalanceSheetCreate, BalanceSheetUpdate]):
    model = BalanceSheet


class CashFlowStatementService(StatementServiceBase[CashFlowStatement, CashFlowStatementCreate, CashFlowStatementUpdate]):
    model = CashFlowStatement


def _to_decimal(value: object) -> Decimal:
    return Decimal(str(value))


def build_ratio_frame(income: IncomeStatement, balance: BalanceSheet, cash_flow: CashFlowStatement) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "revenue": _to_decimal(income.revenue),
                "gross_profit": _to_decimal(income.gross_profit),
                "operating_income": _to_decimal(income.operating_income),
                "net_income": _to_decimal(income.net_income),
                "total_current_assets": _to_decimal(balance.total_current_assets),
                "inventory": _to_decimal(balance.inventory),
                "total_current_liabilities": _to_decimal(balance.total_current_liabilities),
                "total_liabilities": _to_decimal(balance.total_liabilities),
                "total_equity": _to_decimal(balance.total_equity),
                "total_assets": _to_decimal(balance.total_assets),
                "cash_from_operations": _to_decimal(cash_flow.cash_from_operations),
                "capex": _to_decimal(cash_flow.capex),
                "interest_expense": abs(_to_decimal(income.interest_expense)),
                "ebitda": _to_decimal(income.ebitda),
            }
        ]
    )
