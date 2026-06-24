from __future__ import annotations

from datetime import date, datetime, timezone
import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.filing import Filing
from app.models.guidance_record import GuidanceRecord
from app.models.news_event import NewsEvent
from app.models.research_document import ResearchDocument
from app.models.research_risk import ResearchRisk

EVENT_TYPE_KEYWORDS: dict[str, list[str]] = {
    "Product Launch": ["launch", "unveil", "new product", "rollout"],
    "Acquisition": ["acquire", "acquisition", "buyout", "merger"],
    "Divestiture": ["divest", "sell business", "spin off", "asset sale"],
    "Earnings Announcement": ["earnings", "results", "quarterly report"],
    "Regulatory Action": ["regulator", "regulatory", "investigation", "sec"],
    "Lawsuit": ["lawsuit", "litigation", "sued", "legal action"],
    "Management Change": ["ceo", "cfo", "appointed", "resigned", "executive"],
    "Debt Issuance": ["debt issuance", "notes offering", "bond issuance"],
    "Stock Buyback": ["buyback", "repurchase"],
    "Dividend Announcement": ["dividend", "payout"],
    "Partnership": ["partnership", "collaboration", "joint venture"],
    "Cybersecurity Incident": ["cyber", "breach", "ransomware", "data leak"],
    "Supply Chain Event": ["supply chain", "supplier", "logistics disruption"],
}

EVENT_CATEGORY_MAP: dict[str, str] = {
    "Product Launch": "growth",
    "Acquisition": "corporate_action",
    "Divestiture": "corporate_action",
    "Earnings Announcement": "financial_reporting",
    "Regulatory Action": "regulatory",
    "Lawsuit": "legal",
    "Management Change": "leadership",
    "Debt Issuance": "capital_structure",
    "Stock Buyback": "capital_allocation",
    "Dividend Announcement": "capital_allocation",
    "Partnership": "strategic",
    "Cybersecurity Incident": "operational_risk",
    "Supply Chain Event": "operational_risk",
}

RISK_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Regulatory": ["regulation", "regulatory", "compliance", "government"],
    "Competitive": ["competition", "competitive", "market share", "rival"],
    "Operational": ["operations", "execution", "manufacturing", "downtime"],
    "Cybersecurity": ["cyber", "breach", "security", "ransomware"],
    "Supply Chain": ["supply chain", "supplier", "procurement", "logistics"],
    "Customer Concentration": ["customer concentration", "top customer", "single customer"],
}

GUIDANCE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "Revenue guidance",
        re.compile(
            r"(revenue|sales)[^\.\n]{0,80}(guidance|expect|expected|project|outlook)[^\.\n]{0,80}(\d+(?:\.\d+)?\s?%\s?(?:to|-)?\s?\d*(?:\.\d+)?\s?%?|\$\s?\d+(?:\.\d+)?\s?(?:billion|million|bn|m)?)",
            re.IGNORECASE,
        ),
    ),
    (
        "Earnings guidance",
        re.compile(
            r"(eps|earnings)[^\.\n]{0,80}(guidance|expect|expected|outlook)[^\.\n]{0,80}(\$?\s?\d+(?:\.\d+)?)",
            re.IGNORECASE,
        ),
    ),
    (
        "Margin guidance",
        re.compile(
            r"(margin|operating margin|gross margin)[^\.\n]{0,80}(guidance|expect|expected|outlook)[^\.\n]{0,80}(\d+(?:\.\d+)?\s?%\s?(?:to|-)?\s?\d*(?:\.\d+)?\s?%?)",
            re.IGNORECASE,
        ),
    ),
    (
        "CapEx guidance",
        re.compile(
            r"(capex|capital expenditure)[^\.\n]{0,80}(guidance|expect|expected|outlook|plan)[^\.\n]{0,80}(\$\s?\d+(?:\.\d+)?\s?(?:billion|million|bn|m)?)",
            re.IGNORECASE,
        ),
    ),
]

POSITIVE_WORDS = {
    "beat",
    "growth",
    "strong",
    "improve",
    "upside",
    "record",
    "expansion",
    "profit",
    "outperform",
}
NEGATIVE_WORDS = {
    "miss",
    "decline",
    "weak",
    "pressure",
    "risk",
    "downside",
    "loss",
    "breach",
    "lawsuit",
    "investigation",
}


class ResearchIntelligenceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ingest_filing_document(
        self,
        company_id: int,
        document_type: str,
        source: str,
        publication_date: date,
        title: str,
        content: str,
        source_document_url: str | None = None,
    ) -> ResearchDocument:
        findings = {
            "business_overview": self.extract_business_overview(content),
            "operating_segments": self._extract_segment_mentions(content),
            "geographic_exposure": self._extract_geo_mentions(content),
            "key_products_and_services": self._extract_product_mentions(content),
            "mda": self.extract_mda(content),
        }

        document = ResearchDocument(
            company_id=company_id,
            document_type=document_type,
            source=source,
            publication_date=publication_date,
            title=title,
            summary=self._summarize_text(content),
            source_document_url=source_document_url,
            key_findings=findings,
            confidence_score=0.78,
            supporting_text_excerpt=self._best_excerpt(content),
        )
        self.db.add(document)
        self.db.flush()

        for extracted in self.extract_risks(content):
            self.db.add(
                ResearchRisk(
                    company_id=company_id,
                    research_document_id=document.id,
                    publication_date=publication_date,
                    risk_category=extracted["risk_category"],
                    description=extracted["description"],
                    severity=extracted["severity"],
                    confidence=extracted["confidence"],
                    source_document=title,
                    supporting_text_excerpt=extracted["supporting_text_excerpt"],
                )
            )

        self.db.commit()
        self.db.refresh(document)
        return document

    def ingest_earnings_call_transcript(
        self,
        company_id: int,
        publication_date: date,
        title: str,
        transcript_text: str,
        source: str = "Earnings Call",
    ) -> ResearchDocument:
        commentary = self.extract_management_commentary(transcript_text)
        document = ResearchDocument(
            company_id=company_id,
            document_type="earnings_call",
            source=source,
            publication_date=publication_date,
            title=title,
            summary=self._summarize_text(transcript_text),
            key_findings={"management_commentary": commentary},
            confidence_score=0.74,
            supporting_text_excerpt=self._best_excerpt(transcript_text),
        )
        self.db.add(document)
        self.db.flush()

        for guidance in self.extract_guidance(transcript_text):
            self.db.add(
                GuidanceRecord(
                    company_id=company_id,
                    research_document_id=document.id,
                    publication_date=publication_date,
                    guidance_type=guidance["guidance_type"],
                    guidance_value=guidance["guidance_value"],
                    confidence=guidance["confidence"],
                    source_document=title,
                    supporting_text_excerpt=guidance["supporting_text_excerpt"],
                )
            )

        self.db.commit()
        self.db.refresh(document)
        return document

    def ingest_news_article(
        self,
        company_id: int,
        publication_date: date,
        source: str,
        headline: str,
        body: str,
    ) -> NewsEvent:
        combined_text = f"{headline}. {body}"
        event_type, confidence = self.classify_event_type(combined_text)
        sentiment = self.score_sentiment(combined_text)
        importance = self.score_importance(event_type, sentiment)

        document = ResearchDocument(
            company_id=company_id,
            document_type="news",
            source=source,
            publication_date=publication_date,
            title=headline,
            summary=self._summarize_text(body),
            key_findings={"event_type": event_type, "sentiment": sentiment},
            confidence_score=confidence,
            supporting_text_excerpt=self._best_excerpt(combined_text),
        )
        self.db.add(document)
        self.db.flush()

        event = NewsEvent(
            company_id=company_id,
            research_document_id=document.id,
            publication_date=publication_date,
            event_type=event_type,
            event_category=EVENT_CATEGORY_MAP.get(event_type, "general"),
            sentiment=sentiment,
            importance_score=importance,
            confidence_score=confidence,
            source=source,
            headline=headline,
            event_summary=self._summarize_text(body),
            source_document=headline,
            supporting_text_excerpt=self._best_excerpt(combined_text),
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_research_payload(self, ticker: str) -> dict[str, Any] | None:
        company = self._get_company(ticker)
        if company is None:
            return None

        self._bootstrap_documents_from_filings(company)

        documents = self._documents(company.id)
        risks = self._risks(company.id)
        guidance = self._guidance(company.id)
        news = self._news(company.id)

        return {
            "ticker": company.ticker,
            "company_id": company.id,
            "generated_at": datetime.now(timezone.utc),
            "summary_card": {
                "total_documents": len(documents),
                "total_risks": len(risks),
                "total_guidance_updates": len(guidance),
                "total_news_events": len(news),
                "negative_news_count": sum(1 for row in news if row.sentiment == "Negative"),
            },
            "documents": documents,
            "key_risks": risks[:10],
            "guidance_updates": guidance[:10],
            "recent_news_events": news[:10],
        }

    def get_risks_payload(self, ticker: str) -> dict[str, Any] | None:
        company = self._get_company(ticker)
        if company is None:
            return None
        return {
            "ticker": company.ticker,
            "company_id": company.id,
            "risks": self._risks(company.id),
        }

    def get_guidance_payload(self, ticker: str) -> dict[str, Any] | None:
        company = self._get_company(ticker)
        if company is None:
            return None
        return {
            "ticker": company.ticker,
            "company_id": company.id,
            "guidance": self._guidance(company.id),
        }

    def get_news_payload(self, ticker: str) -> dict[str, Any] | None:
        company = self._get_company(ticker)
        if company is None:
            return None
        return {
            "ticker": company.ticker,
            "company_id": company.id,
            "news_events": self._news(company.id),
        }

    def get_timeline_payload(self, ticker: str) -> dict[str, Any] | None:
        company = self._get_company(ticker)
        if company is None:
            return None

        documents = self._documents(company.id)
        document_lookup: dict[str, dict[str, Any]] = {
            row.title: {
                "document_type": row.document_type,
                "source_document_url": row.source_document_url,
            }
            for row in documents
        }

        timeline: list[dict[str, Any]] = []
        for row in documents:
            timeline.append(
                {
                    "date": row.publication_date,
                    "item_type": "Document",
                    "title": row.title,
                    "summary": row.summary,
                    "filing_type": row.document_type,
                    "confidence_score": float(row.confidence_score),
                    "source_document": row.title,
                    "source_document_url": row.source_document_url,
                }
            )
        for row in self._risks(company.id):
            doc = document_lookup.get(row.source_document, {})
            timeline.append(
                {
                    "date": row.publication_date,
                    "item_type": "Risk",
                    "title": f"{row.risk_category} risk",
                    "summary": row.description,
                    "filing_type": doc.get("document_type"),
                    "confidence_score": float(row.confidence),
                    "source_document": row.source_document,
                    "source_document_url": doc.get("source_document_url"),
                }
            )
        for row in self._guidance(company.id):
            doc = document_lookup.get(row.source_document, {})
            timeline.append(
                {
                    "date": row.publication_date,
                    "item_type": "Guidance",
                    "title": row.guidance_type,
                    "summary": row.guidance_value,
                    "filing_type": doc.get("document_type"),
                    "confidence_score": float(row.confidence),
                    "source_document": row.source_document,
                    "source_document_url": doc.get("source_document_url"),
                }
            )
        for row in self._news(company.id):
            doc = document_lookup.get(row.source_document, {})
            timeline.append(
                {
                    "date": row.publication_date,
                    "item_type": "News",
                    "title": row.headline,
                    "summary": row.event_summary,
                    "filing_type": doc.get("document_type"),
                    "sentiment": row.sentiment,
                    "importance_score": row.importance_score,
                    "confidence_score": float(row.confidence_score),
                    "source_document": row.source_document,
                    "source_document_url": doc.get("source_document_url"),
                }
            )

        timeline.sort(key=lambda item: item["date"], reverse=True)
        return {
            "ticker": company.ticker,
            "company_id": company.id,
            "timeline": timeline,
        }

    def extract_business_overview(self, text: str) -> str:
        section = self._extract_section(text, ["business", "overview"], ["risk factors", "management discussion"])
        return section or self._summarize_text(text)

    def extract_mda(self, text: str) -> dict[str, list[str]]:
        section = self._extract_section(
            text,
            ["management discussion", "mda", "management's discussion"],
            ["quantitative", "risk factors", "financial statements"],
        )
        return {
            "growth_initiatives": self._collect_sentences(section, ["growth", "expand", "initiative"]),
            "margin_discussion": self._collect_sentences(section, ["margin", "profitability"]),
            "capital_allocation_plans": self._collect_sentences(section, ["capital allocation", "buyback", "dividend", "debt reduction"]),
            "cost_reduction_programs": self._collect_sentences(section, ["cost", "efficiency", "optimization", "restructuring"]),
            "strategic_priorities": self._collect_sentences(section, ["strategy", "priority", "roadmap"]),
        }

    def extract_risks(self, text: str) -> list[dict[str, Any]]:
        section = self._extract_section(text, ["risk factors", "risks"], ["unresolved staff comments", "properties", "legal proceedings"])
        if not section:
            section = text

        sentences = self._split_sentences(section)
        extracted: list[dict[str, Any]] = []
        for sentence in sentences:
            category = self.categorize_risk(sentence)
            if category is None:
                continue
            extracted.append(
                {
                    "risk_category": category,
                    "description": sentence,
                    "severity": self._severity(sentence),
                    "confidence": self._confidence_from_text(sentence),
                    "supporting_text_excerpt": sentence[:280],
                }
            )

        return extracted[:20]

    def extract_guidance(self, text: str) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for guidance_type, pattern in GUIDANCE_PATTERNS:
            for match in pattern.finditer(text):
                value = match.group(3).strip()
                excerpt = match.group(0).strip()
                records.append(
                    {
                        "guidance_type": guidance_type,
                        "guidance_value": value,
                        "confidence": self._confidence_from_text(excerpt),
                        "supporting_text_excerpt": excerpt[:280],
                    }
                )

        unique: dict[tuple[str, str], dict[str, Any]] = {}
        for row in records:
            unique[(row["guidance_type"], row["guidance_value"])] = row
        return list(unique.values())

    def extract_management_commentary(self, text: str) -> dict[str, list[str]]:
        return {
            "positive_developments": self._collect_sentences(text, ["strong", "improved", "momentum", "record"]),
            "negative_developments": self._collect_sentences(text, ["headwind", "pressure", "decline", "challenge"]),
            "strategic_initiatives": self._collect_sentences(text, ["strategy", "initiative", "roadmap", "investment"]),
        }

    def classify_event_type(self, text: str) -> tuple[str, float]:
        lower = text.lower()
        best_type = "Earnings Announcement" if "earnings" in lower else "Partnership"
        best_hits = 0
        for event_type, keywords in EVENT_TYPE_KEYWORDS.items():
            hits = sum(1 for keyword in keywords if keyword in lower)
            if hits > best_hits:
                best_hits = hits
                best_type = event_type

        confidence = min(0.95, 0.5 + (best_hits * 0.12))
        return best_type, round(confidence, 4)

    def score_sentiment(self, text: str) -> str:
        tokens = re.findall(r"[a-zA-Z']+", text.lower())
        positives = sum(1 for token in tokens if token in POSITIVE_WORDS)
        negatives = sum(1 for token in tokens if token in NEGATIVE_WORDS)
        if positives - negatives >= 2:
            return "Positive"
        if negatives - positives >= 2:
            return "Negative"
        return "Neutral"

    def score_importance(self, event_type: str, sentiment: str) -> int:
        base = {
            "Regulatory Action": 9,
            "Lawsuit": 8,
            "Cybersecurity Incident": 9,
            "Acquisition": 8,
            "Debt Issuance": 7,
            "Earnings Announcement": 8,
        }.get(event_type, 6)

        if sentiment == "Negative":
            base += 1
        if sentiment == "Positive" and event_type in {"Product Launch", "Partnership", "Stock Buyback"}:
            base += 1

        return max(1, min(10, base))

    def categorize_risk(self, text: str) -> str | None:
        lower = text.lower()
        for category, keywords in RISK_CATEGORY_KEYWORDS.items():
            if any(keyword in lower for keyword in keywords):
                return category
        return None

    def _severity(self, text: str) -> str:
        lower = text.lower()
        if any(token in lower for token in ["material", "severe", "critical", "substantial"]):
            return "High"
        if any(token in lower for token in ["significant", "elevated", "notable"]):
            return "Medium"
        return "Low"

    def _confidence_from_text(self, text: str) -> float:
        lower = text.lower()
        signal_terms = ["expect", "guidance", "plan", "will", "material", "risk"]
        hits = sum(1 for term in signal_terms if term in lower)
        return round(min(0.95, 0.5 + hits * 0.08), 4)

    def _bootstrap_documents_from_filings(self, company: Company) -> None:
        existing_titles = {
            row.title
            for row in self.db.query(ResearchDocument)
            .filter(ResearchDocument.company_id == company.id)
            .all()
        }

        filings = (
            self.db.query(Filing)
            .filter(Filing.company_id == company.id)
            .order_by(Filing.filing_date.desc())
            .all()
        )

        added = False
        for filing in filings:
            title = f"{filing.form_type} {filing.fiscal_year} {filing.fiscal_period} ({filing.accession_number})"
            if title in existing_titles:
                continue
            self.db.add(
                ResearchDocument(
                    company_id=company.id,
                    document_type=filing.form_type,
                    source="SEC EDGAR",
                    publication_date=filing.filing_date or date(filing.fiscal_year, 1, 1),
                    title=title,
                    summary=f"Auto-ingested {filing.form_type} filing for fiscal {filing.fiscal_year} {filing.fiscal_period}.",
                    source_document_url=filing.source_document_url,
                    key_findings={
                        "business_overview": "Primary filing metadata ingested. Full text extraction can enrich this record.",
                        "mda": {},
                    },
                    confidence_score=0.55,
                    supporting_text_excerpt=f"Accession {filing.accession_number} from form {filing.form_type}",
                )
            )
            added = True

        if added:
            self.db.commit()

    def _documents(self, company_id: int) -> list[ResearchDocument]:
        return (
            self.db.query(ResearchDocument)
            .filter(ResearchDocument.company_id == company_id)
            .order_by(ResearchDocument.publication_date.desc(), ResearchDocument.created_at.desc())
            .all()
        )

    def _risks(self, company_id: int) -> list[ResearchRisk]:
        return (
            self.db.query(ResearchRisk)
            .filter(ResearchRisk.company_id == company_id)
            .order_by(ResearchRisk.publication_date.desc(), ResearchRisk.created_at.desc())
            .all()
        )

    def _guidance(self, company_id: int) -> list[GuidanceRecord]:
        return (
            self.db.query(GuidanceRecord)
            .filter(GuidanceRecord.company_id == company_id)
            .order_by(GuidanceRecord.publication_date.desc(), GuidanceRecord.created_at.desc())
            .all()
        )

    def _news(self, company_id: int) -> list[NewsEvent]:
        return (
            self.db.query(NewsEvent)
            .filter(NewsEvent.company_id == company_id)
            .order_by(NewsEvent.publication_date.desc(), NewsEvent.created_at.desc())
            .all()
        )

    def _get_company(self, ticker: str) -> Company | None:
        return self.db.query(Company).filter(Company.ticker == ticker.upper()).one_or_none()

    def _summarize_text(self, text: str, max_sentences: int = 2) -> str:
        sentences = self._split_sentences(text)
        if not sentences:
            return "No summary available."
        return " ".join(sentences[:max_sentences])[:1000]

    def _best_excerpt(self, text: str) -> str:
        sentences = self._split_sentences(text)
        if not sentences:
            return ""
        return sentences[0][:320]

    def _split_sentences(self, text: str) -> list[str]:
        chunks = re.split(r"(?<=[.!?])\s+", text)
        return [chunk.strip() for chunk in chunks if chunk and chunk.strip()]

    def _extract_section(self, text: str, start_markers: list[str], end_markers: list[str]) -> str:
        lower = text.lower()
        start_index = -1
        for marker in start_markers:
            idx = lower.find(marker)
            if idx != -1:
                start_index = idx
                break

        if start_index == -1:
            return ""

        end_index = len(text)
        for marker in end_markers:
            idx = lower.find(marker, start_index + 1)
            if idx != -1:
                end_index = min(end_index, idx)

        return text[start_index:end_index].strip()

    def _collect_sentences(self, text: str, keywords: list[str], max_items: int = 5) -> list[str]:
        if not text:
            return []
        out: list[str] = []
        for sentence in self._split_sentences(text):
            lower = sentence.lower()
            if any(keyword in lower for keyword in keywords):
                out.append(sentence)
            if len(out) >= max_items:
                break
        return out

    def _extract_segment_mentions(self, text: str) -> list[str]:
        return self._collect_sentences(text, ["segment", "business unit", "division"])[:4]

    def _extract_geo_mentions(self, text: str) -> list[str]:
        return self._collect_sentences(text, ["geographic", "international", "region", "country"])[:4]

    def _extract_product_mentions(self, text: str) -> list[str]:
        return self._collect_sentences(text, ["product", "service", "platform", "solution"])[:4]
