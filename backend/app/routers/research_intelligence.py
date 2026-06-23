from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.research import GuidanceResponse, NewsResponse, ResearchResponse, RisksResponse, TimelineResponse
from app.services.research_intelligence_service import ResearchIntelligenceService

router = APIRouter(tags=["research-intelligence"])


@router.get("/research/{ticker}", response_model=ResearchResponse)
def get_research(ticker: str, db: Session = Depends(get_db)):
    payload = ResearchIntelligenceService(db).get_research_payload(ticker)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    return payload


@router.get("/risks/{ticker}", response_model=RisksResponse)
def get_risks(ticker: str, db: Session = Depends(get_db)):
    payload = ResearchIntelligenceService(db).get_risks_payload(ticker)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    return payload


@router.get("/guidance/{ticker}", response_model=GuidanceResponse)
def get_guidance(ticker: str, db: Session = Depends(get_db)):
    payload = ResearchIntelligenceService(db).get_guidance_payload(ticker)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    return payload


@router.get("/news/{ticker}", response_model=NewsResponse)
def get_news(ticker: str, db: Session = Depends(get_db)):
    payload = ResearchIntelligenceService(db).get_news_payload(ticker)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    return payload


@router.get("/timeline/{ticker}", response_model=TimelineResponse)
def get_timeline(ticker: str, db: Session = Depends(get_db)):
    payload = ResearchIntelligenceService(db).get_timeline_payload(ticker)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    return payload
