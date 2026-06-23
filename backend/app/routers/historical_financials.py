from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.historical_financials import CompanyHistoricalRead, FinancialsBundleResponse, SyncResponse
from app.services.historical_financials_service import HistoricalFinancialsService
from app.services.sec_client import SECClientError

router = APIRouter(tags=["historical-financials"])


@router.get("/company/{ticker}", response_model=CompanyHistoricalRead)
def get_company_by_ticker(ticker: str, db: Session = Depends(get_db)):
    company = HistoricalFinancialsService(db).get_company(ticker)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found. Run /sync/{ticker} first.")
    return company


@router.get("/financials/{ticker}", response_model=FinancialsBundleResponse)
def get_financials_by_ticker(ticker: str, db: Session = Depends(get_db)):
    bundle = HistoricalFinancialsService(db).get_financials_bundle(ticker)
    if bundle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No financials found. Run /sync/{ticker} first.")
    return bundle


@router.post("/sync/{ticker}", response_model=SyncResponse)
def sync_financials_by_ticker(
    ticker: str,
    max_periods: int = Query(default=8, ge=1, le=20),
    db: Session = Depends(get_db),
):
    try:
        return HistoricalFinancialsService(db).sync_ticker(ticker=ticker, max_periods=max_periods)
    except SECClientError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed. Check DATABASE_URL and PostgreSQL credentials.",
        ) from exc
