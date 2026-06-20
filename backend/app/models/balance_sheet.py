from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, StatementMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company


class BalanceSheet(Base, StatementMixin, TimestampMixin):
    __tablename__ = "balance_sheets"
    __table_args__ = (
        UniqueConstraint("company_id", "fiscal_year", "fiscal_period", name="uq_balance_company_year_period"),
        Index("ix_balance_company_year", "company_id", "fiscal_year"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company: Mapped["Company"] = relationship(back_populates="balance_sheets")
    fiscal_period: Mapped[str] = mapped_column(String(8), nullable=False, index=True, default="FY")

    cash: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    shareholder_equity: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    total_debt: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    cash_and_equivalents: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    accounts_receivable: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    inventory: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_current_assets: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    property_plant_equipment: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_assets: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    accounts_payable: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    short_term_debt: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_current_liabilities: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    long_term_debt: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_liabilities: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_equity: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
