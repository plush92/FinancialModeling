from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, StatementMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company


class IncomeStatement(Base, StatementMixin, TimestampMixin):
    __tablename__ = "income_statements"
    __table_args__ = (
        UniqueConstraint("company_id", "fiscal_year", "fiscal_period", name="uq_income_company_year_period"),
        Index("ix_income_company_year", "company_id", "fiscal_year"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company: Mapped["Company"] = relationship(back_populates="income_statements")
    fiscal_period: Mapped[str] = mapped_column(String(8), nullable=False, index=True, default="FY")

    eps: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    revenue: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    cogs: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    gross_profit: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    operating_expenses: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    ebitda: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    depreciation_and_amortization: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    operating_income: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    interest_expense: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    pretax_income: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    tax_expense: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    net_income: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
