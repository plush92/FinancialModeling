from decimal import Decimal

from app.models.base import PeriodType
from app.models.financial_ratio import FinancialRatio
from app.schemas.financial_ratio import FinancialRatioCreate, FinancialRatioUpdate
from app.services.base import CRUDService
from app.services.statement_service import BalanceSheetService, CashFlowStatementService, IncomeStatementService, build_ratio_frame


def _ratio_value(numerator: object, denominator: object) -> Decimal:
    numerator_decimal = Decimal(str(numerator))
    denominator_decimal = Decimal(str(denominator))
    if denominator_decimal == 0:
        return Decimal("0")
    return numerator_decimal / denominator_decimal


class FinancialRatioService(CRUDService[FinancialRatio, FinancialRatioCreate, FinancialRatioUpdate]):
    model = FinancialRatio

    def calculate_from_statements(self, company_id: int, fiscal_year: int, period_type: PeriodType):
        income = IncomeStatementService(self.db).get_for_period(company_id, fiscal_year, period_type)
        balance = BalanceSheetService(self.db).get_for_period(company_id, fiscal_year, period_type)
        cash_flow = CashFlowStatementService(self.db).get_for_period(company_id, fiscal_year, period_type)

        if income is None or balance is None or cash_flow is None:
            raise ValueError("Income statement, balance sheet, and cash flow statement are all required for ratio calculation.")

        frame = build_ratio_frame(income, balance, cash_flow)
        row = frame.iloc[0]

        ratio_payload = FinancialRatioCreate(
            company_id=company_id,
            fiscal_year=fiscal_year,
            period_type=period_type,
            currency=income.currency,
            gross_margin=_ratio_value(row["gross_profit"], row["revenue"]),
            operating_margin=_ratio_value(row["operating_income"], row["revenue"]),
            net_margin=_ratio_value(row["net_income"], row["revenue"]),
            current_ratio=_ratio_value(row["total_current_assets"], balance.total_current_liabilities),
            quick_ratio=_ratio_value(row["total_current_assets"] - row["inventory"], balance.total_current_liabilities),
            debt_to_equity=_ratio_value(row["total_liabilities"], row["total_equity"]),
            return_on_assets=_ratio_value(row["net_income"], row["total_assets"]),
            return_on_equity=_ratio_value(row["net_income"], row["total_equity"]),
            free_cash_flow_margin=_ratio_value(row["cash_from_operations"] - row["capex"], row["revenue"]),
            interest_coverage=_ratio_value(row["ebitda"], row["interest_expense"]),
        )

        return self.create(ratio_payload)
