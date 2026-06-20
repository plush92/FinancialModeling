from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class MappingException(Base, TimestampMixin):
    __tablename__ = "mapping_exceptions"
    __table_args__ = (
        Index("ix_mapping_company_filing", "company_id", "filing_id"),
        Index("ix_mapping_field", "attempted_field"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    xbrl_tag: Mapped[str | None] = mapped_column(String(128), nullable=True)
    attempted_field: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    filing_id: Mapped[int | None] = mapped_column(ForeignKey("filings.id"), nullable=True, index=True)
