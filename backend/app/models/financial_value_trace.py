from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class FinancialValueTrace(Base, TimestampMixin):
    __tablename__ = "financial_value_traces"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "filing_id",
            "statement_type",
            "fiscal_year",
            "fiscal_period",
            "canonical_field",
            name="uq_trace_company_filing_statement_field",
        ),
        Index("ix_trace_company_filing", "company_id", "filing_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    filing_id: Mapped[int] = mapped_column(ForeignKey("filings.id"), nullable=False, index=True)
    statement_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    fiscal_period: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    canonical_field: Mapped[str] = mapped_column(String(64), nullable=False)
    value_numeric: Mapped[Decimal | None] = mapped_column(Numeric(24, 6), nullable=True)
    source_tag: Mapped[str | None] = mapped_column(String(128), nullable=True)
    accession_number: Mapped[str] = mapped_column(String(32), nullable=False)
    filing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_document_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
