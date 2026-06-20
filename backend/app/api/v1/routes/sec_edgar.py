from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.sec_edgar_service import SECIngestionError, SecEdgarService

router = APIRouter(prefix="/sec-edgar", tags=["sec-edgar"])


@router.post("/ingest/{ticker}", status_code=status.HTTP_201_CREATED)
def ingest_sec_filings(ticker: str, filing_count: int = Query(default=1, ge=1, le=10), db: Session = Depends(get_db)):
    try:
        return SecEdgarService(db).ingest_ticker(ticker, filing_count=filing_count)
    except SECIngestionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
