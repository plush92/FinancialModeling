from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company


class Filing(Base, TimestampMixin):
    __tablename__ = "filings"
    __table_args__ = (
        UniqueConstraint("company_id", "accession_number", name="uq_filing_company_accession"),
        Index("ix_filing_company_period", "company_id", "fiscal_year", "fiscal_period"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    accession_number: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    form_type: Mapped[str] = mapped_column(String(12), nullable=False)
    filing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    fiscal_period: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    source_document_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    company: Mapped["Company"] = relationship(back_populates="filings")
