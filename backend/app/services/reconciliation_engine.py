from __future__ import annotations

from decimal import Decimal


class ReconciliationEngine:
    @staticmethod
    def _is_within_tolerance(expected: Decimal, actual: Decimal, tolerance_pct: Decimal) -> bool:
        baseline = abs(expected) if expected != 0 else Decimal("1")
        tolerance_amount = baseline * tolerance_pct / Decimal("100")
        return abs(actual - expected) <= tolerance_amount

    @classmethod
    def balance_sheet_identity(
        cls,
        total_assets: Decimal,
        total_liabilities: Decimal,
        shareholder_equity: Decimal,
        tolerance_pct: Decimal,
    ) -> bool:
        return cls._is_within_tolerance(total_assets, total_liabilities + shareholder_equity, tolerance_pct)

    @classmethod
    def gross_profit_consistency(
        cls,
        revenue: Decimal,
        cogs: Decimal,
        gross_profit: Decimal,
        tolerance_pct: Decimal,
    ) -> bool:
        return cls._is_within_tolerance(revenue - cogs, gross_profit, tolerance_pct)

    @classmethod
    def net_income_consistency(
        cls,
        pretax_income: Decimal,
        tax_expense: Decimal,
        net_income: Decimal,
        tolerance_pct: Decimal,
    ) -> bool:
        return cls._is_within_tolerance(pretax_income - tax_expense, net_income, tolerance_pct)

    @classmethod
    def cash_rollforward(
        cls,
        beginning_cash: Decimal,
        net_change_in_cash: Decimal,
        ending_cash: Decimal,
        tolerance_pct: Decimal,
    ) -> bool:
        return cls._is_within_tolerance(beginning_cash + net_change_in_cash, ending_cash, tolerance_pct)

    @classmethod
    def free_cash_flow_consistency(
        cls,
        operating_cash_flow: Decimal,
        capex: Decimal,
        free_cash_flow: Decimal,
        tolerance_pct: Decimal,
    ) -> bool:
        return cls._is_within_tolerance(operating_cash_flow - capex, free_cash_flow, tolerance_pct)
