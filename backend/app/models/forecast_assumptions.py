from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, ForeignKey, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company


class ForecastAssumptionSet(Base, TimestampMixin):
    __tablename__ = "forecast_assumption_sets"
    __table_args__ = (
        UniqueConstraint("company_id", "version", "scenario", name="uq_forecast_assumption_company_version_scenario"),
        Index("ix_forecast_assumption_company_created", "company_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    scenario: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    assumptions: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    source_context: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    company: Mapped["Company"] = relationship(back_populates="forecast_assumption_sets")
