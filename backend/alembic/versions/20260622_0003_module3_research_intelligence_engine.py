"""module3_research_intelligence_engine

Revision ID: 20260622_0003
Revises: 20260622_0002
Create Date: 2026-06-22
"""

from alembic import op
import sqlalchemy as sa


revision = "20260622_0003"
down_revision = "20260622_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "research_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("publication_date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("source_document_url", sa.String(length=1024), nullable=True),
        sa.Column("key_findings", sa.JSON(), nullable=False),
        sa.Column("extraction_timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("confidence_score", sa.Numeric(6, 4), nullable=False),
        sa.Column("supporting_text_excerpt", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_research_documents_company_id", "research_documents", ["company_id"], unique=False)
    op.create_index("ix_research_documents_document_type", "research_documents", ["document_type"], unique=False)
    op.create_index("ix_research_documents_publication_date", "research_documents", ["publication_date"], unique=False)
    op.create_index("ix_research_document_company_date", "research_documents", ["company_id", "publication_date"], unique=False)
    op.create_index("ix_research_document_company_type", "research_documents", ["company_id", "document_type"], unique=False)

    op.create_table(
        "research_risks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("research_document_id", sa.Integer(), nullable=True),
        sa.Column("publication_date", sa.Date(), nullable=False),
        sa.Column("risk_category", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("confidence", sa.Numeric(6, 4), nullable=False),
        sa.Column("source_document", sa.String(length=512), nullable=False),
        sa.Column("extraction_timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("supporting_text_excerpt", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["research_document_id"], ["research_documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_research_risks_company_id", "research_risks", ["company_id"], unique=False)
    op.create_index("ix_research_risks_research_document_id", "research_risks", ["research_document_id"], unique=False)
    op.create_index("ix_research_risks_publication_date", "research_risks", ["publication_date"], unique=False)
    op.create_index("ix_research_risks_risk_category", "research_risks", ["risk_category"], unique=False)
    op.create_index("ix_research_risk_company_date", "research_risks", ["company_id", "publication_date"], unique=False)
    op.create_index("ix_research_risk_company_category", "research_risks", ["company_id", "risk_category"], unique=False)

    op.create_table(
        "guidance_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("research_document_id", sa.Integer(), nullable=True),
        sa.Column("publication_date", sa.Date(), nullable=False),
        sa.Column("guidance_type", sa.String(length=64), nullable=False),
        sa.Column("guidance_value", sa.String(length=255), nullable=False),
        sa.Column("confidence", sa.Numeric(6, 4), nullable=False),
        sa.Column("source_document", sa.String(length=512), nullable=False),
        sa.Column("extraction_timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("supporting_text_excerpt", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["research_document_id"], ["research_documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_guidance_records_company_id", "guidance_records", ["company_id"], unique=False)
    op.create_index("ix_guidance_records_research_document_id", "guidance_records", ["research_document_id"], unique=False)
    op.create_index("ix_guidance_records_publication_date", "guidance_records", ["publication_date"], unique=False)
    op.create_index("ix_guidance_records_guidance_type", "guidance_records", ["guidance_type"], unique=False)
    op.create_index("ix_guidance_company_date", "guidance_records", ["company_id", "publication_date"], unique=False)
    op.create_index("ix_guidance_company_type", "guidance_records", ["company_id", "guidance_type"], unique=False)

    op.create_table(
        "news_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("research_document_id", sa.Integer(), nullable=True),
        sa.Column("publication_date", sa.Date(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("event_category", sa.String(length=64), nullable=False),
        sa.Column("sentiment", sa.String(length=16), nullable=False),
        sa.Column("importance_score", sa.Integer(), nullable=False),
        sa.Column("confidence_score", sa.Numeric(6, 4), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("headline", sa.String(length=512), nullable=False),
        sa.Column("event_summary", sa.Text(), nullable=False),
        sa.Column("source_document", sa.String(length=512), nullable=False),
        sa.Column("extraction_timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("supporting_text_excerpt", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["research_document_id"], ["research_documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_news_events_company_id", "news_events", ["company_id"], unique=False)
    op.create_index("ix_news_events_research_document_id", "news_events", ["research_document_id"], unique=False)
    op.create_index("ix_news_events_publication_date", "news_events", ["publication_date"], unique=False)
    op.create_index("ix_news_events_event_type", "news_events", ["event_type"], unique=False)
    op.create_index("ix_news_events_event_category", "news_events", ["event_category"], unique=False)
    op.create_index("ix_news_events_sentiment", "news_events", ["sentiment"], unique=False)
    op.create_index("ix_news_event_company_date", "news_events", ["company_id", "publication_date"], unique=False)
    op.create_index("ix_news_event_company_type", "news_events", ["company_id", "event_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_news_event_company_type", table_name="news_events")
    op.drop_index("ix_news_event_company_date", table_name="news_events")
    op.drop_index("ix_news_events_sentiment", table_name="news_events")
    op.drop_index("ix_news_events_event_category", table_name="news_events")
    op.drop_index("ix_news_events_event_type", table_name="news_events")
    op.drop_index("ix_news_events_publication_date", table_name="news_events")
    op.drop_index("ix_news_events_research_document_id", table_name="news_events")
    op.drop_index("ix_news_events_company_id", table_name="news_events")
    op.drop_table("news_events")

    op.drop_index("ix_guidance_company_type", table_name="guidance_records")
    op.drop_index("ix_guidance_company_date", table_name="guidance_records")
    op.drop_index("ix_guidance_records_guidance_type", table_name="guidance_records")
    op.drop_index("ix_guidance_records_publication_date", table_name="guidance_records")
    op.drop_index("ix_guidance_records_research_document_id", table_name="guidance_records")
    op.drop_index("ix_guidance_records_company_id", table_name="guidance_records")
    op.drop_table("guidance_records")

    op.drop_index("ix_research_risk_company_category", table_name="research_risks")
    op.drop_index("ix_research_risk_company_date", table_name="research_risks")
    op.drop_index("ix_research_risks_risk_category", table_name="research_risks")
    op.drop_index("ix_research_risks_publication_date", table_name="research_risks")
    op.drop_index("ix_research_risks_research_document_id", table_name="research_risks")
    op.drop_index("ix_research_risks_company_id", table_name="research_risks")
    op.drop_table("research_risks")

    op.drop_index("ix_research_document_company_type", table_name="research_documents")
    op.drop_index("ix_research_document_company_date", table_name="research_documents")
    op.drop_index("ix_research_documents_publication_date", table_name="research_documents")
    op.drop_index("ix_research_documents_document_type", table_name="research_documents")
    op.drop_index("ix_research_documents_company_id", table_name="research_documents")
    op.drop_table("research_documents")
