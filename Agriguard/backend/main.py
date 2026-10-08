import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.config import settings
from backend.database import Base, engine, get_db
from backend.models import *  # noqa: F401, F403
from backend.routers import auth_routes, report_routes, chat_routes, expert_routes, metrics_routes
from backend.services.classifier import classifier
from backend.schemas import SupportedCropsResponse
from backend.utils.memory import log_memory

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("agriguard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management for DB initialization, demo seeding, and memory tracking."""
    # 1. Create DB tables
    Base.metadata.create_all(bind=engine)
    
    # 2. Memory Telemetry at boot
    log_memory("FastAPI Startup")

    # 3. Seed Demo Data on startup if configured
    if settings.SEED_DEMO:
        try:
            from scripts.seed import seed_database
            seed_database()
        except Exception as e:
            logger.warning(f"Demo seeding warning: {e}")

    yield
    logger.info("AgriGuard backend shutting down.")


app = FastAPI(
    title="AgriGuard API",
    description="Local AI-powered crop disease detection, severity analysis, and advisory assistant",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for local development / cloud deployments
origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]
if not origins or "*" in origins:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for uploads and overlays
upload_path = Path(settings.UPLOAD_DIR)
upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_path.resolve())), name="uploads")
app.mount("/api/uploads", StaticFiles(directory=str(upload_path.resolve())), name="api_uploads")

# Health Check (Requirement: GET /health returning {"status":"ok"})
@app.get("/health", tags=["General"])
def health_check():
    return {"status": "ok"}

@app.get("/api/health", tags=["General"])
def api_health_check():
    return {"status": "ok"}


# Mount API Routers under /api
api_prefix = "/api"
app.include_router(auth_routes.router, prefix=api_prefix)
app.include_router(report_routes.router, prefix=api_prefix)
app.include_router(chat_routes.router, prefix=api_prefix)
app.include_router(expert_routes.router, prefix=api_prefix)
app.include_router(metrics_routes.router, prefix=api_prefix)

# Also include under root for direct / legacy testing compatibility
app.include_router(auth_routes.router)
app.include_router(report_routes.router)
app.include_router(chat_routes.router)
app.include_router(expert_routes.router)
app.include_router(metrics_routes.router)


@app.get("/api/supported-crops", response_model=SupportedCropsResponse, tags=["General"])
@app.get("/supported-crops", response_model=SupportedCropsResponse, tags=["General"])
def get_supported_crops():
    """Returns all supported crops and classes recognized by the model."""
    crops = classifier.get_supported_crops()
    return SupportedCropsResponse(
        crops=crops,
        total_classes=len(classifier.class_names),
        classes=classifier.class_names,
        disclaimer="AgriGuard's local model is trained specifically on the crops and diseases listed here. Uploading photos of other crops may lead to inaccurate identification."
    )


# Static SPA Frontend Serving (Requirement 1)
frontend_dist = Path("frontend/dist")
if frontend_dist.exists():
    # Mount assets folder
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir.resolve())), name="assets")

    # Catch-all SPA route
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(request: Request, full_path: str):
        # Do not intercept API, health, or upload routes
        if full_path.startswith("api/") or full_path.startswith("uploads/") or full_path == "health":
            return JSONResponse(status_code=404, content={"detail": "Not Found"})

        # Check if specific file exists in dist (e.g., favicon.ico, vite.svg)
        target_file = frontend_dist / full_path
        if full_path and target_file.exists() and target_file.is_file():
            return FileResponse(str(target_file.resolve()))

        # Otherwise fallback to index.html for React client-side routing
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file.resolve()))
        return JSONResponse(status_code=404, content={"detail": "Frontend not built"})
