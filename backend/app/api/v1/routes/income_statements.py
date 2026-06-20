from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.base import PeriodType
from app.schemas.income_statement import IncomeStatementCreate, IncomeStatementRead, IncomeStatementUpdate
from app.services.statement_service import IncomeStatementService

router = APIRouter(prefix="/income-statements", tags=["income-statements"])


@router.get("", response_model=list[IncomeStatementRead])
def list_income_statements(
    company_id: int | None = Query(default=None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    service = IncomeStatementService(db)
    if company_id is None:
        return service.list(skip=skip, limit=limit)
    return service.list_by_company(company_id, skip=skip, limit=limit)


@router.post("", response_model=IncomeStatementRead, status_code=status.HTTP_201_CREATED)
def create_income_statement(payload: IncomeStatementCreate, db: Session = Depends(get_db)):
    return IncomeStatementService(db).create(payload)


@router.get("/{statement_id}", response_model=IncomeStatementRead)
def get_income_statement(statement_id: int, db: Session = Depends(get_db)):
    statement = IncomeStatementService(db).get(statement_id)
    if statement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income statement not found.")
    return statement


@router.patch("/{statement_id}", response_model=IncomeStatementRead)
def update_income_statement(statement_id: int, payload: IncomeStatementUpdate, db: Session = Depends(get_db)):
    service = IncomeStatementService(db)
    statement = service.get(statement_id)
    if statement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income statement not found.")
    return service.update(statement, payload)


@router.delete("/{statement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_income_statement(statement_id: int, db: Session = Depends(get_db)):
    service = IncomeStatementService(db)
    statement = service.get(statement_id)
    if statement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income statement not found.")
    service.delete(statement)
    return None
