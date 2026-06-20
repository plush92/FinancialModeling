from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.base import PeriodType
from app.schemas.financial_ratio import FinancialRatioCreate, FinancialRatioRead, FinancialRatioUpdate
from app.services.financial_ratio_service import FinancialRatioService

router = APIRouter(prefix="/financial-ratios", tags=["financial-ratios"])


@router.get("", response_model=list[FinancialRatioRead])
def list_financial_ratios(
    company_id: int | None = Query(default=None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    service = FinancialRatioService(db)
    if company_id is None:
        return service.list(skip=skip, limit=limit)
    return db.query(service.model).filter(service.model.company_id == company_id).offset(skip).limit(limit).all()


@router.post("", response_model=FinancialRatioRead, status_code=status.HTTP_201_CREATED)
def create_financial_ratio(payload: FinancialRatioCreate, db: Session = Depends(get_db)):
    return FinancialRatioService(db).create(payload)


@router.post("/calculate", response_model=FinancialRatioRead, status_code=status.HTTP_201_CREATED)
def calculate_financial_ratio(
    company_id: int = Query(..., gt=0),
    fiscal_year: int = Query(..., ge=1900, le=2100),
    period_type: PeriodType = Query(...),
    db: Session = Depends(get_db),
):
    try:
        return FinancialRatioService(db).calculate_from_statements(company_id, fiscal_year, period_type)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{ratio_id}", response_model=FinancialRatioRead)
def get_financial_ratio(ratio_id: int, db: Session = Depends(get_db)):
    ratio = FinancialRatioService(db).get(ratio_id)
    if ratio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Financial ratio not found.")
    return ratio


@router.patch("/{ratio_id}", response_model=FinancialRatioRead)
def update_financial_ratio(ratio_id: int, payload: FinancialRatioUpdate, db: Session = Depends(get_db)):
    service = FinancialRatioService(db)
    ratio = service.get(ratio_id)
    if ratio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Financial ratio not found.")
    return service.update(ratio, payload)


@router.delete("/{ratio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_financial_ratio(ratio_id: int, db: Session = Depends(get_db)):
    service = FinancialRatioService(db)
    ratio = service.get(ratio_id)
    if ratio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Financial ratio not found.")
    service.delete(ratio)
    return None
