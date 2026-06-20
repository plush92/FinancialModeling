"""module1_historical_slice

Revision ID: 20260620_0001
Revises:
Create Date: 2026-06-20
"""

from alembic import op
import sqlalchemy as sa


revision = "20260620_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("company_name", sa.String(length=255), nullable=True))
    op.execute("UPDATE companies SET company_name = name WHERE company_name IS NULL")
    op.alter_column("companies", "company_name", nullable=False)

    op.add_column("income_statements", sa.Column("fiscal_period", sa.String(length=8), nullable=True))
    op.add_column("income_statements", sa.Column("eps", sa.Numeric(18, 4), nullable=True))
    op.execute("UPDATE income_statements SET fiscal_period = 'FY' WHERE fiscal_period IS NULL")
    op.execute("UPDATE income_statements SET eps = 0 WHERE eps IS NULL")
    op.alter_column("income_statements", "fiscal_period", nullable=False)
    op.alter_column("income_statements", "eps", nullable=False)
    op.create_unique_constraint(
        "uq_income_company_year_period",
        "income_statements",
        ["company_id", "fiscal_year", "fiscal_period"],
    )

    op.add_column("balance_sheets", sa.Column("fiscal_period", sa.String(length=8), nullable=True))
    op.add_column("balance_sheets", sa.Column("cash", sa.Numeric(18, 2), nullable=True))
    op.add_column("balance_sheets", sa.Column("shareholder_equity", sa.Numeric(18, 2), nullable=True))
    op.add_column("balance_sheets", sa.Column("total_debt", sa.Numeric(18, 2), nullable=True))
    op.execute("UPDATE balance_sheets SET fiscal_period = 'FY' WHERE fiscal_period IS NULL")
    op.execute("UPDATE balance_sheets SET cash = cash_and_equivalents WHERE cash IS NULL")
    op.execute("UPDATE balance_sheets SET shareholder_equity = total_equity WHERE shareholder_equity IS NULL")
    op.execute("UPDATE balance_sheets SET total_debt = COALESCE(short_term_debt, 0) + COALESCE(long_term_debt, 0) WHERE total_debt IS NULL")
    op.alter_column("balance_sheets", "fiscal_period", nullable=False)
    op.alter_column("balance_sheets", "cash", nullable=False)
    op.alter_column("balance_sheets", "shareholder_equity", nullable=False)
    op.alter_column("balance_sheets", "total_debt", nullable=False)
    op.create_unique_constraint(
        "uq_balance_company_year_period",
        "balance_sheets",
        ["company_id", "fiscal_year", "fiscal_period"],
    )

    op.add_column("cash_flow_statements", sa.Column("fiscal_period", sa.String(length=8), nullable=True))
    op.add_column("cash_flow_statements", sa.Column("operating_cash_flow", sa.Numeric(18, 2), nullable=True))
    op.add_column("cash_flow_statements", sa.Column("free_cash_flow", sa.Numeric(18, 2), nullable=True))
    op.execute("UPDATE cash_flow_statements SET fiscal_period = 'FY' WHERE fiscal_period IS NULL")
    op.execute("UPDATE cash_flow_statements SET operating_cash_flow = cash_from_operations WHERE operating_cash_flow IS NULL")
    op.execute("UPDATE cash_flow_statements SET free_cash_flow = COALESCE(cash_from_operations, 0) - COALESCE(capex, 0) WHERE free_cash_flow IS NULL")
    op.alter_column("cash_flow_statements", "fiscal_period", nullable=False)
    op.alter_column("cash_flow_statements", "operating_cash_flow", nullable=False)
    op.alter_column("cash_flow_statements", "free_cash_flow", nullable=False)
    op.create_unique_constraint(
        "uq_cashflow_company_year_period",
        "cash_flow_statements",
        ["company_id", "fiscal_year", "fiscal_period"],
    )

    op.create_table(
        "ingestion_exceptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ingestion_ticker_created", "ingestion_exceptions", ["ticker", "created_at"])
    op.create_index("ix_ingestion_company_created", "ingestion_exceptions", ["company_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_ingestion_company_created", table_name="ingestion_exceptions")
    op.drop_index("ix_ingestion_ticker_created", table_name="ingestion_exceptions")
    op.drop_table("ingestion_exceptions")

    op.drop_constraint("uq_cashflow_company_year_period", "cash_flow_statements", type_="unique")
    op.drop_column("cash_flow_statements", "free_cash_flow")
    op.drop_column("cash_flow_statements", "operating_cash_flow")
    op.drop_column("cash_flow_statements", "fiscal_period")

    op.drop_constraint("uq_balance_company_year_period", "balance_sheets", type_="unique")
    op.drop_column("balance_sheets", "total_debt")
    op.drop_column("balance_sheets", "shareholder_equity")
    op.drop_column("balance_sheets", "cash")
    op.drop_column("balance_sheets", "fiscal_period")

    op.drop_constraint("uq_income_company_year_period", "income_statements", type_="unique")
    op.drop_column("income_statements", "eps")
    op.drop_column("income_statements", "fiscal_period")

    op.drop_column("companies", "company_name")
