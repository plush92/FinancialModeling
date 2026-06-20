from decimal import Decimal

from app.models.base import PeriodType
from app.models.company import Company
from app.models.income_statement import IncomeStatement
from app.models.mapping_exception import MappingException
from app.models.validation_issue import ValidationIssue
from app.services.financials_validation_service import FinancialsValidationService


def test_missing_data_handling_logs_warning_issue(db_session):
    db = db_session
    company = Company(ticker="TEST", company_name="Test Co", name="Test Co", currency="USD", fiscal_year_end_month=12)
    db.add(company)
    db.commit()
    db.refresh(company)

    validator = FinancialsValidationService(db)
    validator.validate_required_values(
        ticker="TEST",
        statement_type="income_statement",
        fiscal_year=2025,
        fiscal_period="FY",
        required_values={"revenue": None, "net_income": Decimal("10")},
        company_id=company.id,
    )
    db.commit()

    assert db.query(ValidationIssue).count() == 1


def test_duplicate_period_detection(db_session):
    db = db_session
    company = Company(ticker="DUPL", company_name="Duplicate Co", name="Duplicate Co", currency="USD", fiscal_year_end_month=12)
    db.add(company)
    db.commit()
    db.refresh(company)

    statement = IncomeStatement(
        company_id=company.id,
        fiscal_year=2025,
        fiscal_period="FY",
        period_type=PeriodType.annual,
        currency="USD",
        revenue=Decimal("100"),
        cogs=Decimal("0"),
        gross_profit=Decimal("100"),
        operating_expenses=Decimal("0"),
        ebitda=Decimal("100"),
        depreciation_and_amortization=Decimal("0"),
        operating_income=Decimal("100"),
        interest_expense=Decimal("0"),
        pretax_income=Decimal("100"),
        tax_expense=Decimal("0"),
        net_income=Decimal("100"),
        eps=Decimal("1.0"),
    )
    db.add(statement)
    db.commit()

    validator = FinancialsValidationService(db)
    assert validator.is_duplicate_period(IncomeStatement, company.id, 2025, "FY")


def test_mapping_validation_logging(db_session):
    db = db_session
    company = Company(ticker="MAP", company_name="Mapping Co", name="Mapping Co", currency="USD", fiscal_year_end_month=12)
    db.add(company)
    db.commit()
    db.refresh(company)

    validator = FinancialsValidationService(db)
    validator.log_mapping_exception(
        company_id=company.id,
        filing_id=None,
        attempted_field="revenue",
        xbrl_tag=None,
        confidence=0.0,
        notes="Tag not found",
    )
    db.commit()

    assert db.query(MappingException).count() == 1
