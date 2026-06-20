from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.balance_sheet import BalanceSheetCreate, BalanceSheetRead, BalanceSheetUpdate
from app.services.statement_service import BalanceSheetService

router = APIRouter(prefix="/balance-sheets", tags=["balance-sheets"])


@router.get("", response_model=list[BalanceSheetRead])
def list_balance_sheets(
    company_id: int | None = Query(default=None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    service = BalanceSheetService(db)
    if company_id is None:
        return service.list(skip=skip, limit=limit)
    return service.list_by_company(company_id, skip=skip, limit=limit)


@router.post("", response_model=BalanceSheetRead, status_code=status.HTTP_201_CREATED)
def create_balance_sheet(payload: BalanceSheetCreate, db: Session = Depends(get_db)):
    return BalanceSheetService(db).create(payload)


@router.get("/{statement_id}", response_model=BalanceSheetRead)
def get_balance_sheet(statement_id: int, db: Session = Depends(get_db)):
    statement = BalanceSheetService(db).get(statement_id)
    if statement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Balance sheet not found.")
    return statement


@router.patch("/{statement_id}", response_model=BalanceSheetRead)
def update_balance_sheet(statement_id: int, payload: BalanceSheetUpdate, db: Session = Depends(get_db)):
    service = BalanceSheetService(db)
    statement = service.get(statement_id)
    if statement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Balance sheet not found.")
    return service.update(statement, payload)


@router.delete("/{statement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_balance_sheet(statement_id: int, db: Session = Depends(get_db)):
    service = BalanceSheetService(db)
    statement = service.get(statement_id)
    if statement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Balance sheet not found.")
    service.delete(statement)
    return None
