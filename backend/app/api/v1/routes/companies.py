from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate
from app.services.company_service import CompanyService

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[CompanyRead])
def list_companies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return CompanyService(db).list(skip=skip, limit=limit)


@router.post("", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    service = CompanyService(db)
    if service.get_by_ticker(payload.ticker):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Company ticker already exists.")
    return service.create(payload)


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = CompanyService(db).get(company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    return company


@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(company_id: int, payload: CompanyUpdate, db: Session = Depends(get_db)):
    service = CompanyService(db)
    company = service.get(company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    if payload.ticker and payload.ticker != company.ticker and service.get_by_ticker(payload.ticker):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Company ticker already exists.")
    return service.update(company, payload)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: int, db: Session = Depends(get_db)):
    service = CompanyService(db)
    company = service.get(company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    service.delete(company)
    return None
