# Backend Architecture

This backend is a FastAPI service designed to store and serve financial model data backed by PostgreSQL and SQLAlchemy.

## What lives here

- `app/main.py` creates the FastAPI application and wires the router tree.
- `app/core/config.py` loads environment-driven settings such as the database URL.
- `app/db/session.py` creates the SQLAlchemy engine and session factory.
- `app/db/base.py` imports all models so metadata is registered in one place.
- `app/models/` contains SQLAlchemy ORM models for companies and financial statements.
- `app/schemas/` contains Pydantic request and response models.
- `app/services/` contains business logic, CRUD operations, and ratio calculations.
- `app/api/v1/routes/` contains the API endpoints for each resource.

## Supported resources

- Companies
- Income Statements
- Balance Sheets
- Cash Flow Statements
- Financial Ratios

## Local development

1. Create a `.env` file from `.env.example` and update `DATABASE_URL`.
2. Install dependencies with `pip install -r requirements.txt`.
3. Start the API with `uvicorn backend.app.main:app --reload`.

## File purpose overview

- `app/models/company.py`: company master data and relationships.
- `app/models/income_statement.py`: annual or quarterly income statement rows.
- `app/models/balance_sheet.py`: balance sheet rows.
- `app/models/cash_flow_statement.py`: cash flow statement rows.
- `app/models/financial_ratio.py`: derived and stored valuation ratios.
- `app/schemas/*.py`: typed payloads for create, update, and read operations.
- `app/services/company_service.py`: company CRUD and lookup helpers.
- `app/services/statement_service.py`: shared CRUD logic for financial statements.
- `app/services/financial_ratio_service.py`: Pandas-driven ratio calculations.
- `app/services/sec_edgar_service.py`: SEC ticker lookup, filing download, XBRL mapping, and persistence.
- `app/api/v1/routes/*.py`: REST endpoints for each domain object.
