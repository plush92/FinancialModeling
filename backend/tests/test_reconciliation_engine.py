from decimal import Decimal

from app.services.reconciliation_engine import ReconciliationEngine


def test_balance_sheet_identity_passes_within_tolerance():
    assert ReconciliationEngine.balance_sheet_identity(
        total_assets=Decimal("1000"),
        total_liabilities=Decimal("600"),
        shareholder_equity=Decimal("400"),
        tolerance_pct=Decimal("0.5"),
    )


def test_balance_sheet_identity_fails_outside_tolerance():
    assert not ReconciliationEngine.balance_sheet_identity(
        total_assets=Decimal("1000"),
        total_liabilities=Decimal("600"),
        shareholder_equity=Decimal("350"),
        tolerance_pct=Decimal("0.5"),
    )


def test_free_cash_flow_consistency():
    assert ReconciliationEngine.free_cash_flow_consistency(
        operating_cash_flow=Decimal("120"),
        capex=Decimal("20"),
        free_cash_flow=Decimal("100"),
        tolerance_pct=Decimal("0.1"),
    )
