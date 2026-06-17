"""HealthManage API entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base, engine
from app.routers import admin, auth, conditions, consent, medications, patients, record
import app.models  # noqa: F401  (register all tables)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # prototype; use Alembic in prod
    yield


app = FastAPI(title=f"{settings.APP_NAME} API", version="0.2.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware,
                   allow_origins=["http://localhost:5173", "http://localhost:3000"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(consent.router)
app.include_router(medications.router)
app.include_router(patients.router)
app.include_router(record.router)
app.include_router(conditions.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "app": settings.APP_NAME}
