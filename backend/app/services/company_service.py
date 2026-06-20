from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate
from app.services.base import CRUDService


class CompanyService(CRUDService[Company, CompanyCreate, CompanyUpdate]):
    model = Company

    def get_by_ticker(self, ticker: str):
        return self.db.query(Company).filter(Company.ticker == ticker.upper()).one_or_none()
