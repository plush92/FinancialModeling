from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, StatementMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company


class CashFlowStatement(Base, StatementMixin, TimestampMixin):
    __tablename__ = "cash_flow_statements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company: Mapped["Company"] = relationship(back_populates="cash_flow_statements")

    net_income: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    depreciation_and_amortization: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    change_in_working_capital: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    cash_from_operations: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    capex: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    cash_from_investing: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    debt_issued: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    debt_repaid: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    dividends_paid: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    cash_from_financing: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    net_change_in_cash: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    ending_cash: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
