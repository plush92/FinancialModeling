from datetime import date

from app.models.company import Company
from app.services.research_intelligence_service import ResearchIntelligenceService


def test_event_classification_and_sentiment(db_session):
    db = db_session
    service = ResearchIntelligenceService(db)

    event_type, confidence = service.classify_event_type("The company announced a new product launch and partnership.")
    assert event_type in {"Product Launch", "Partnership"}
    assert confidence >= 0.5

    sentiment = service.score_sentiment("Strong growth and record profit drove upside momentum.")
    assert sentiment == "Positive"


def test_risk_categorization_and_extraction(db_session):
    db = db_session
    service = ResearchIntelligenceService(db)

    text = (
        "Risk Factors. We face regulatory compliance challenges and cybersecurity breach exposure. "
        "Supply chain disruption may materially affect operations."
    )
    risks = service.extract_risks(text)
    assert len(risks) >= 2
    categories = {row["risk_category"] for row in risks}
    assert "Regulatory" in categories or "Cybersecurity" in categories


def test_guidance_extraction(db_session):
    db = db_session
    service = ResearchIntelligenceService(db)

    transcript = (
        "We expect revenue guidance of 8% to 10% year over year. "
        "We also expect EPS guidance of $3.20 for the next quarter."
    )
    guidance = service.extract_guidance(transcript)
    assert len(guidance) >= 1
    guidance_types = {item["guidance_type"] for item in guidance}
    assert "Revenue guidance" in guidance_types or "Earnings guidance" in guidance_types


def test_news_ingestion_and_timeline_generation(db_session):
    db = db_session
    company = Company(ticker="RSCH", company_name="Research Co", name="Research Co", currency="USD", fiscal_year_end_month=12)
    db.add(company)
    db.commit()
    db.refresh(company)

    service = ResearchIntelligenceService(db)
    service.ingest_news_article(
        company_id=company.id,
        publication_date=date(2026, 5, 1),
        source="Financial Times",
        headline="Research Co announces stock buyback",
        body="The board approved a large repurchase program after strong earnings.",
    )

    timeline_payload = service.get_timeline_payload("RSCH")
    assert timeline_payload is not None
    assert len(timeline_payload["timeline"]) >= 1
    assert timeline_payload["timeline"][0]["item_type"] in {"News", "Document", "Risk", "Guidance"}


def test_document_parsing_and_storage(db_session):
    db = db_session
    company = Company(ticker="DOCS", company_name="Docs Co", name="Docs Co", currency="USD", fiscal_year_end_month=12)
    db.add(company)
    db.commit()
    db.refresh(company)

    service = ResearchIntelligenceService(db)
    doc = service.ingest_filing_document(
        company_id=company.id,
        document_type="10-K",
        source="SEC",
        publication_date=date(2026, 2, 15),
        title="Docs Co 10-K",
        content=(
            "Business Overview. We operate product segments in cloud services. "
            "Risk Factors. Regulatory investigation and customer concentration could impact results. "
            "Management Discussion and Analysis. Our strategy includes cost optimization and expansion."
        ),
    )
    assert doc.id is not None

    payload = service.get_research_payload("DOCS")
    assert payload is not None
    assert payload["summary_card"]["total_documents"] >= 1
    assert len(payload["key_risks"]) >= 1
