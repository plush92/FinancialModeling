from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, StatementMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company


class IncomeStatement(Base, StatementMixin, TimestampMixin):
    __tablename__ = "income_statements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company: Mapped["Company"] = relationship(back_populates="income_statements")

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
