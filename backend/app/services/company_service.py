from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate
from app.services.base import CRUDService


class CompanyService(CRUDService[Company, CompanyCreate, CompanyUpdate]):
    model = Company

    def create(self, obj_in: CompanyCreate):
        payload = obj_in.model_dump()
        canonical_name = payload.get("company_name") or payload.get("name")
        if canonical_name is None:
            raise ValueError("Either company_name or name is required.")
        payload["company_name"] = canonical_name
        payload["name"] = canonical_name
        payload["ticker"] = payload["ticker"].upper()
        db_obj = Company(**payload)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: Company, obj_in: CompanyUpdate):
        payload = obj_in.model_dump(exclude_unset=True)
        if "ticker" in payload and payload["ticker"]:
            payload["ticker"] = payload["ticker"].upper()
        if "company_name" in payload or "name" in payload:
            canonical_name = payload.get("company_name") or payload.get("name")
            if canonical_name is not None:
                payload["company_name"] = canonical_name
                payload["name"] = canonical_name
        for field_name, value in payload.items():
            setattr(db_obj, field_name, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_by_ticker(self, ticker: str):
        return self.db.query(Company).filter(Company.ticker == ticker.upper()).one_or_none()
