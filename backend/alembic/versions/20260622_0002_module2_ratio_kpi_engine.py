"""module2_ratio_kpi_engine

Revision ID: 20260622_0002
Revises: 20260620_0001
Create Date: 2026-06-22
"""

from alembic import op
import sqlalchemy as sa


revision = "20260622_0002"
down_revision = "20260620_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "financial_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("fiscal_period", sa.String(length=8), nullable=False),
        sa.Column(
            "period_type",
            sa.Enum("annual", "quarterly", name="period_type", create_type=False),
            nullable=False,
        ),
        sa.Column("metric_name", sa.String(length=80), nullable=False),
        sa.Column("metric_value", sa.Numeric(24, 8), nullable=True),
        sa.Column("formula", sa.Text(), nullable=False),
        sa.Column("inputs_used", sa.JSON(), nullable=False),
        sa.Column("source_metrics", sa.JSON(), nullable=False),
        sa.Column("calculation_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id",
            "fiscal_year",
            "fiscal_period",
            "metric_name",
            "calculation_version",
            name="uq_financial_metric_period_name_version",
        ),
    )
    op.create_index("ix_financial_metrics_company_id", "financial_metrics", ["company_id"], unique=False)
    op.create_index("ix_financial_metrics_fiscal_year", "financial_metrics", ["fiscal_year"], unique=False)
    op.create_index("ix_financial_metrics_fiscal_period", "financial_metrics", ["fiscal_period"], unique=False)
    op.create_index("ix_financial_metrics_period_type", "financial_metrics", ["period_type"], unique=False)
    op.create_index("ix_financial_metrics_metric_name", "financial_metrics", ["metric_name"], unique=False)
    op.create_index(
        "ix_financial_metric_company_period",
        "financial_metrics",
        ["company_id", "fiscal_year", "fiscal_period"],
        unique=False,
    )
    op.create_index(
        "ix_financial_metric_company_name",
        "financial_metrics",
        ["company_id", "metric_name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_financial_metric_company_name", table_name="financial_metrics")
    op.drop_index("ix_financial_metric_company_period", table_name="financial_metrics")
    op.drop_index("ix_financial_metrics_metric_name", table_name="financial_metrics")
    op.drop_index("ix_financial_metrics_period_type", table_name="financial_metrics")
    op.drop_index("ix_financial_metrics_fiscal_period", table_name="financial_metrics")
    op.drop_index("ix_financial_metrics_fiscal_year", table_name="financial_metrics")
    op.drop_index("ix_financial_metrics_company_id", table_name="financial_metrics")
    op.drop_table("financial_metrics")
