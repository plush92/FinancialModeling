from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.forecast import ForecastRequest, ForecastResponse, ForecastScenariosResponse
from app.services.forecast_service import ForecastService

router = APIRouter(tags=["forecast-engine"])


@router.post("/forecast/{ticker}", response_model=ForecastResponse)
def create_forecast(ticker: str, body: ForecastRequest, db: Session = Depends(get_db)):
    try:
        payload = ForecastService(db).get_forecast_payload(
            ticker=ticker,
            scenario=body.scenario,
            assumptions_version=body.assumptions_version,
            horizon_years=body.horizon_years,
            assumptions_override=body.assumptions_override,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found or insufficient historical data.")
    return payload


@router.get("/forecast/{ticker}", response_model=ForecastResponse)
def get_forecast(ticker: str, scenario: str = "base", assumptions_version: str = "latest", db: Session = Depends(get_db)):
    try:
        payload = ForecastService(db).get_forecast_payload(
            ticker=ticker,
            scenario=scenario,
            assumptions_version=assumptions_version,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found or insufficient historical data.")
    return payload


@router.get("/forecast/{ticker}/scenarios", response_model=ForecastScenariosResponse)
def get_forecast_scenarios(ticker: str, assumptions_version: str = "latest", db: Session = Depends(get_db)):
    try:
        payload = ForecastService(db).get_all_scenarios_payload(ticker=ticker, assumptions_version=assumptions_version)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found or insufficient historical data.")
    return payload
