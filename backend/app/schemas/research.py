from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ResearchDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    document_type: str
    source: str
    publication_date: date
    title: str
    summary: str
    source_document_url: str | None
    key_findings: dict[str, Any]
    extraction_timestamp: datetime
    confidence_score: float
    supporting_text_excerpt: str | None
    created_at: datetime


class ResearchRiskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    publication_date: date
    risk_category: str
    description: str
    severity: str
    confidence: float
    source_document: str
    extraction_timestamp: datetime
    supporting_text_excerpt: str | None
    created_at: datetime


class GuidanceRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    publication_date: date
    guidance_type: str
    guidance_value: str
    confidence: float
    source_document: str
    extraction_timestamp: datetime
    supporting_text_excerpt: str | None
    created_at: datetime


class NewsEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    publication_date: date
    event_type: str
    event_category: str
    sentiment: str
    importance_score: int
    confidence_score: float
    source: str
    headline: str
    event_summary: str
    source_document: str
    extraction_timestamp: datetime
    supporting_text_excerpt: str | None
    created_at: datetime


class TimelineItem(BaseModel):
    date: date
    item_type: str
    title: str
    summary: str
    sentiment: str | None = None
    importance_score: int | None = None
    confidence_score: float | None = None
    source_document: str | None = None


class ResearchSummaryCardData(BaseModel):
    total_documents: int
    total_risks: int
    total_guidance_updates: int
    total_news_events: int
    negative_news_count: int


class ResearchResponse(BaseModel):
    ticker: str
    company_id: int
    generated_at: datetime
    summary_card: ResearchSummaryCardData
    documents: list[ResearchDocumentRead]
    key_risks: list[ResearchRiskRead]
    guidance_updates: list[GuidanceRecordRead]
    recent_news_events: list[NewsEventRead]


class RisksResponse(BaseModel):
    ticker: str
    company_id: int
    risks: list[ResearchRiskRead]


class GuidanceResponse(BaseModel):
    ticker: str
    company_id: int
    guidance: list[GuidanceRecordRead]


class NewsResponse(BaseModel):
    ticker: str
    company_id: int
    news_events: list[NewsEventRead]


class TimelineResponse(BaseModel):
    ticker: str
    company_id: int
    timeline: list[TimelineItem]
