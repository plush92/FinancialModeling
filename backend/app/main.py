from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.api import api_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.routers.data_quality import router as data_quality_router
from app.routers.historical_financials import router as historical_router
from app.routers.ratio_engine import router as ratio_engine_router
from app.routers.research_intelligence import router as research_intelligence_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.project_name, version=settings.version, lifespan=lifespan)
app.include_router(api_router, prefix=settings.api_v1_prefix)
app.include_router(historical_router)
app.include_router(data_quality_router)
app.include_router(ratio_engine_router)
app.include_router(research_intelligence_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
