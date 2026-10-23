from fastapi import FastAPI
from app.api.routes.admin import router as admin_router

from app.api.routes.auth import router as auth_router
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging_config import setup_logging
from app.api.routes.health import router as health_router
from app.api.routes.documents import router as documents_router
from app.core.config import settings
from contextlib import asynccontextmanager
import threading

from app.ai.semantic_classifier import warm_up as warm_up_semantic_model

from app.api.routes.analytics import router as analytics_router
from app.db.mongodb import close_mongodb_connection, connect_to_mongodb

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongodb()

    # Loading the AI model takes a few seconds; do it in the background so
    # the server is usable immediately.
    threading.Thread(target=warm_up_semantic_model, daemon=True).start()

    yield

    await close_mongodb_connection()

setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "AI Document Red Alert Detection System backend is running",
        "docs_url": "/docs",
        "api_prefix": settings.API_V1_PREFIX,
    }

app.include_router(health_router, prefix=settings.API_V1_PREFIX)
app.include_router(documents_router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics_router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)