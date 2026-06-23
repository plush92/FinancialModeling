from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.balance_sheet import BalanceSheet
    from app.models.cash_flow_statement import CashFlowStatement
    from app.models.filing import Filing
    from app.models.guidance_record import GuidanceRecord
    from app.models.news_event import NewsEvent
    from app.models.financial_metric import FinancialMetric
    from app.models.financial_ratio import FinancialRatio
    from app.models.income_statement import IncomeStatement
    from app.models.research_document import ResearchDocument
    from app.models.research_risk import ResearchRisk


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cik: Mapped[int | None] = mapped_column(Integer, unique=True, index=True, nullable=True)
    ticker: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sector: Mapped[str | None] = mapped_column(String(120), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    fiscal_year_end_month: Mapped[int] = mapped_column(Integer, default=12, nullable=False)

    income_statements: Mapped[list["IncomeStatement"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    balance_sheets: Mapped[list["BalanceSheet"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    cash_flow_statements: Mapped[list["CashFlowStatement"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    financial_ratios: Mapped[list["FinancialRatio"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    financial_metrics: Mapped[list["FinancialMetric"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    filings: Mapped[list["Filing"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    research_documents: Mapped[list["ResearchDocument"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    research_risks: Mapped[list["ResearchRisk"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    guidance_records: Mapped[list["GuidanceRecord"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    news_events: Mapped[list["NewsEvent"]] = relationship(back_populates="company", cascade="all, delete-orphan")

