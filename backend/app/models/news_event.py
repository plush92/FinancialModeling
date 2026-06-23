from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.research_document import ResearchDocument


class NewsEvent(Base):
    __tablename__ = "news_events"
    __table_args__ = (
        Index("ix_news_event_company_date", "company_id", "publication_date"),
        Index("ix_news_event_company_type", "company_id", "event_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    research_document_id: Mapped[int | None] = mapped_column(ForeignKey("research_documents.id"), nullable=True, index=True)

    publication_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sentiment: Mapped[str] = mapped_column(String(16), nullable=False, index=True)

    importance_score: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False, default=0.5)

    source: Mapped[str] = mapped_column(String(255), nullable=False)
    headline: Mapped[str] = mapped_column(String(512), nullable=False)
    event_summary: Mapped[str] = mapped_column(Text, nullable=False)

    source_document: Mapped[str] = mapped_column(String(512), nullable=False)
    extraction_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    supporting_text_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    company: Mapped["Company"] = relationship(back_populates="news_events")
    research_document: Mapped["ResearchDocument | None"] = relationship(back_populates="news_events")
