from datetime import datetime

from pydantic import BaseModel


class QualityResponse(BaseModel):
    quality_score: int
    warnings: list[str]
    errors: list[str]


class ValidationIssueRead(BaseModel):
    id: int
    severity: str
    rule_name: str
    description: str
    filing_id: int | None
    created_at: datetime


class MappingExceptionRead(BaseModel):
    id: int
    xbrl_tag: str | None
    attempted_field: str
    confidence: float | None
    notes: str | None
    filing_id: int | None
    created_at: datetime


class IssuesResponse(BaseModel):
    validation_issues: list[ValidationIssueRead]
    mapping_exceptions: list[MappingExceptionRead]
