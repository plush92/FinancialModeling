from datetime import date, datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PeriodType(str, Enum):
    annual = "annual"
    quarterly = "quarterly"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class StatementMixin:
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True, nullable=False)
    fiscal_year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    period_type: Mapped[PeriodType] = mapped_column(SAEnum(PeriodType, name="period_type"), index=True, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    source_accession_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_filing_date: Mapped[date | None] = mapped_column(nullable=True)
    source_form: Mapped[str | None] = mapped_column(String(12), nullable=True)
