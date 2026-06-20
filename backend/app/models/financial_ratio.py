from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, StatementMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company


class FinancialRatio(Base, StatementMixin, TimestampMixin):
    __tablename__ = "financial_ratios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company: Mapped["Company"] = relationship(back_populates="financial_ratios")

    gross_margin: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    operating_margin: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    net_margin: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    current_ratio: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    quick_ratio: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    debt_to_equity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    return_on_assets: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    return_on_equity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    free_cash_flow_margin: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    interest_coverage: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
