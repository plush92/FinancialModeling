from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.data_quality import IssuesResponse, QualityResponse
from app.services.data_quality_service import DataQualityService

router = APIRouter(tags=["data-quality"])


@router.get("/quality/{ticker}", response_model=QualityResponse)
def get_quality(ticker: str, db: Session = Depends(get_db)):
    quality = DataQualityService(db).get_quality(ticker)
    if quality is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    return quality


@router.get("/issues/{ticker}", response_model=IssuesResponse)
def get_issues(ticker: str, db: Session = Depends(get_db)):
    issues = DataQualityService(db).get_issues(ticker)
    if issues is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    return issues
