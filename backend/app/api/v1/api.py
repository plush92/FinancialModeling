from fastapi import APIRouter

from app.api.v1.routes.balance_sheets import router as balance_sheets_router
from app.api.v1.routes.cash_flow_statements import router as cash_flow_statements_router
from app.api.v1.routes.companies import router as companies_router
from app.api.v1.routes.financial_ratios import router as financial_ratios_router
from app.api.v1.routes.income_statements import router as income_statements_router

api_router = APIRouter()

api_router.include_router(companies_router)
api_router.include_router(income_statements_router)
api_router.include_router(balance_sheets_router)
api_router.include_router(cash_flow_statements_router)
api_router.include_router(financial_ratios_router)
