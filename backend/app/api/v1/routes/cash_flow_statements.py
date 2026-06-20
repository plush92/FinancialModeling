from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.cash_flow_statement import CashFlowStatementCreate, CashFlowStatementRead, CashFlowStatementUpdate
from app.services.statement_service import CashFlowStatementService

router = APIRouter(prefix="/cash-flow-statements", tags=["cash-flow-statements"])


@router.get("", response_model=list[CashFlowStatementRead])
def list_cash_flow_statements(
    company_id: int | None = Query(default=None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    service = CashFlowStatementService(db)
    if company_id is None:
        return service.list(skip=skip, limit=limit)
    return service.list_by_company(company_id, skip=skip, limit=limit)


@router.post("", response_model=CashFlowStatementRead, status_code=status.HTTP_201_CREATED)
def create_cash_flow_statement(payload: CashFlowStatementCreate, db: Session = Depends(get_db)):
    return CashFlowStatementService(db).create(payload)


@router.get("/{statement_id}", response_model=CashFlowStatementRead)
def get_cash_flow_statement(statement_id: int, db: Session = Depends(get_db)):
    statement = CashFlowStatementService(db).get(statement_id)
    if statement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cash flow statement not found.")
    return statement


@router.patch("/{statement_id}", response_model=CashFlowStatementRead)
def update_cash_flow_statement(statement_id: int, payload: CashFlowStatementUpdate, db: Session = Depends(get_db)):
    service = CashFlowStatementService(db)
    statement = service.get(statement_id)
    if statement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cash flow statement not found.")
    return service.update(statement, payload)


@router.delete("/{statement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cash_flow_statement(statement_id: int, db: Session = Depends(get_db)):
    service = CashFlowStatementService(db)
    statement = service.get(statement_id)
    if statement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cash flow statement not found.")
    service.delete(statement)
    return None
