from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.base import PeriodType


class FinancialMetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    fiscal_year: int
    fiscal_period: str
    period_type: PeriodType
    metric_name: str
    metric_value: Decimal | None
    formula: str
    inputs_used: dict[str, Any]
    source_metrics: list[str]
    calculation_version: str
    created_at: datetime


class MetricPoint(BaseModel):
    fiscal_year: int
    fiscal_period: str
    value: Decimal | None


class RatioMetricSeries(BaseModel):
    metric_name: str
    display_name: str
    category: str
    unit: str
    formula: str
    source_metrics: list[str]
    latest_inputs_used: dict[str, Any]
    history: list[MetricPoint]
    latest_value: Decimal | None
    trend_direction: str | None


class KPISummary(BaseModel):
    metric_name: str
    display_name: str
    category: str
    unit: str
    value: Decimal | None
    trend_direction: str | None


class RatiosResponse(BaseModel):
    ticker: str
    company_id: int
    calculation_version: str
    generated_at: datetime
    historical_periods: list[dict[str, object]]
    sections: dict[str, list[RatioMetricSeries]]
    kpi_summary: list[KPISummary]


class MetricTrendRead(BaseModel):
    metric_name: str
    display_name: str
    category: str
    latest_value: Decimal | None
    previous_value: Decimal | None
    cagr_3y: Decimal | None
    cagr_5y: Decimal | None
    rolling_average_3_periods: Decimal | None
    trend_direction: str | None


class MetricsResponse(BaseModel):
    ticker: str
    company_id: int
    calculation_version: str
    metrics: list[FinancialMetricRead]


class TrendsResponse(BaseModel):
    ticker: str
    company_id: int
    calculation_version: str
    trends: list[MetricTrendRead]
