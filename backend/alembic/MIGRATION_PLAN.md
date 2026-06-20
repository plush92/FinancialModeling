# Module 1 Migration Plan

## Goal
Introduce canonical historical statement fields, ingestion exception logging, and period-level uniqueness for SEC-synced data.

## Steps
1. Add `company_name` to `companies` and backfill from `name`.
2. Add canonical fields to `income_statements`:
   - `fiscal_period`, `eps`
3. Add canonical fields to `balance_sheets`:
   - `fiscal_period`, `cash`, `shareholder_equity`, `total_debt`
4. Add canonical fields to `cash_flow_statements`:
   - `fiscal_period`, `operating_cash_flow`, `free_cash_flow`
5. Create `ingestion_exceptions` table for failed mappings and validation warnings.
6. Create uniqueness constraints for `company_id + fiscal_year + fiscal_period` on each statement table.
7. Add supporting composite indexes for query speed by ticker/company and year.

## Operational Notes
- Run in maintenance window if existing data volume is high.
- Backfill canonical fields from existing columns where possible.
- Validate row counts before/after migration.
- If backfill fails for some records, log to `ingestion_exceptions` and continue.
