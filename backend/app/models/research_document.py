from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.guidance_record import GuidanceRecord
    from app.models.news_event import NewsEvent
    from app.models.research_risk import ResearchRisk


class ResearchDocument(Base):
    __tablename__ = "research_documents"
    __table_args__ = (
        Index("ix_research_document_company_date", "company_id", "publication_date"),
        Index("ix_research_document_company_type", "company_id", "document_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)

    document_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    publication_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    source_document_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    key_findings: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    extraction_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False, default=0.5)
    supporting_text_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    company: Mapped["Company"] = relationship(back_populates="research_documents")
    risks: Mapped[list["ResearchRisk"]] = relationship(back_populates="research_document", cascade="all, delete-orphan")
    guidance_records: Mapped[list["GuidanceRecord"]] = relationship(back_populates="research_document", cascade="all, delete-orphan")
    news_events: Mapped[list["NewsEvent"]] = relationship(back_populates="research_document", cascade="all, delete-orphan")
