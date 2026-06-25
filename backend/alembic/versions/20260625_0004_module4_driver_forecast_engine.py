"""module4_driver_forecast_engine

Revision ID: 20260625_0004
Revises: 20260622_0003
Create Date: 2026-06-25
"""

from alembic import op
import sqlalchemy as sa


revision = "20260625_0004"
down_revision = "20260622_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "forecast_assumption_sets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("scenario", sa.String(length=16), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("assumptions", sa.JSON(), nullable=False),
        sa.Column("source_context", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "version", "scenario", name="uq_forecast_assumption_company_version_scenario"),
    )
    op.create_index("ix_forecast_assumption_sets_company_id", "forecast_assumption_sets", ["company_id"], unique=False)
    op.create_index("ix_forecast_assumption_sets_version", "forecast_assumption_sets", ["version"], unique=False)
    op.create_index("ix_forecast_assumption_sets_scenario", "forecast_assumption_sets", ["scenario"], unique=False)
    op.create_index("ix_forecast_assumption_company_created", "forecast_assumption_sets", ["company_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_forecast_assumption_company_created", table_name="forecast_assumption_sets")
    op.drop_index("ix_forecast_assumption_sets_scenario", table_name="forecast_assumption_sets")
    op.drop_index("ix_forecast_assumption_sets_version", table_name="forecast_assumption_sets")
    op.drop_index("ix_forecast_assumption_sets_company_id", table_name="forecast_assumption_sets")
    op.drop_table("forecast_assumption_sets")
