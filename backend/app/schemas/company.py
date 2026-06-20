from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CompanyBase(BaseModel):
    cik: int | None = Field(default=None, gt=0)
    ticker: str = Field(min_length=1, max_length=16)
    name: str = Field(min_length=1, max_length=255)
    sector: str | None = Field(default=None, max_length=120)
    industry: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=120)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    fiscal_year_end_month: int = Field(default=12, ge=1, le=12)


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    cik: int | None = Field(default=None, gt=0)
    ticker: str | None = Field(default=None, min_length=1, max_length=16)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    sector: str | None = Field(default=None, max_length=120)
    industry: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=120)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    fiscal_year_end_month: int | None = Field(default=None, ge=1, le=12)


class CompanyRead(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
