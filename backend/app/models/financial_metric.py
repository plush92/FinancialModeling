from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PeriodType

if TYPE_CHECKING:
    from app.models.company import Company


class FinancialMetric(Base):
    __tablename__ = "financial_metrics"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "fiscal_year",
            "fiscal_period",
            "metric_name",
            "calculation_version",
            name="uq_financial_metric_period_name_version",
        ),
        Index("ix_financial_metric_company_period", "company_id", "fiscal_year", "fiscal_period"),
        Index("ix_financial_metric_company_name", "company_id", "metric_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    fiscal_period: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    period_type: Mapped[PeriodType] = mapped_column(SAEnum(PeriodType, name="period_type"), nullable=False, index=True)

    metric_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    metric_value: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)

    formula: Mapped[str] = mapped_column(Text, nullable=False)
    inputs_used: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    source_metrics: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    calculation_version: Mapped[str] = mapped_column(String(32), nullable=False, default="2.0.0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    company: Mapped["Company"] = relationship(back_populates="financial_metrics")
