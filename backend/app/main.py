"""FastAPI application entry point for Environmental Change Detection."""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .routers import analyze_router, results_router

# Setup directory paths
backend_dir = Path(__file__).resolve().parent.parent
storage_dir = backend_dir / "storage"
uploads_dir = storage_dir / "uploads"
outputs_dir = storage_dir / "outputs"

uploads_dir.mkdir(parents=True, exist_ok=True)
outputs_dir.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context: initialize database tables and directories."""
    init_db()
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Environmental Change Detection API",
    description=(
        "Digital Image Processing (DIP) based environmental change detection platform "
        "supporting multi-spectral Sentinel-2 GeoTIFFs and plain RGB satellite images."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for React / Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount outputs as static files for direct browser/frontend display
app.mount("/outputs", StaticFiles(directory=str(outputs_dir)), name="outputs")

# Register API routers under /api
app.include_router(analyze_router, prefix="/api")
app.include_router(results_router, prefix="/api")


@app.get("/api/health")
def health_check():
    """System health check endpoint."""
    return {
        "status": "ok",
        "app": "ChangeDetectionAPI",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

@app.get("/")
def root():
    """Root redirect / information endpoint."""
    return {
        "message": "Environmental Change Detection API is running.",
        "docs_url": "/docs",
        "health_url": "/api/health",
        "usecases_url": "/api/usecases"
    }

