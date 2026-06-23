from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.financial_metric import MetricsResponse, RatiosResponse, TrendsResponse
from app.services.ratio_engine_service import RatioEngineService

router = APIRouter(tags=["ratio-engine"])


@router.get("/ratios/{ticker}", response_model=RatiosResponse)
def get_ratios(ticker: str, db: Session = Depends(get_db)):
    payload = RatioEngineService(db).get_ratios_payload(ticker)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    return payload


@router.get("/metrics/{ticker}", response_model=MetricsResponse)
def get_metrics(ticker: str, db: Session = Depends(get_db)):
    payload = RatioEngineService(db).get_metrics_payload(ticker)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    return payload


@router.get("/trends/{ticker}", response_model=TrendsResponse)
def get_trends(ticker: str, db: Session = Depends(get_db)):
    payload = RatioEngineService(db).get_trends_payload(ticker)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    return payload
