from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ValidationIssue(Base, TimestampMixin):
    __tablename__ = "validation_issues"
    __table_args__ = (
        Index("ix_validation_company_filing", "company_id", "filing_id"),
        Index("ix_validation_severity", "severity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    rule_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    filing_id: Mapped[int | None] = mapped_column(ForeignKey("filings.id"), nullable=True, index=True)
