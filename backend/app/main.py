import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

import sentry_sdk
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.api.routes import auth, datasets, health, jobs, models, dataset_preprocessing, analysis, workflow, dna_discovery
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import BioMLException
from app.models.base import Base

# Configure logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Initialize Sentry for error tracking
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[
            FastApiIntegration(auto_enabling=True),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,
        environment=settings.ENVIRONMENT,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting BioMLStudio API...")
    
    # Create necessary directories
    for directory in ["uploads", "models", "logs", "temp"]:
        Path(directory).mkdir(exist_ok=True)
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    logger.info("🎉 BioMLStudio API started successfully")
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down BioMLStudio API...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered no-code platform for bioinformatics researchers",
    version="1.0.0",
    docs_url=f"/api/{settings.API_VERSION}/docs" if settings.DEBUG else None,
    redoc_url=f"/api/{settings.API_VERSION}/redoc" if settings.DEBUG else None,
    openapi_url=f"/api/{settings.API_VERSION}/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)


# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["biomlstudio.com", "*.biomlstudio.com"]
    )


# Request timing and logging middleware
@app.middleware("http")
async def process_time_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"🔄 {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log response
    logger.info(f"✅ {request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    
    return response


# Exception handlers
@app.exception_handler(BioMLException)
async def bioml_exception_handler(request: Request, exc: BioMLException):
    logger.error(f"BioML Exception: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "timestamp": time.time(),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP Exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "timestamp": time.time(),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error. Please try again later.",
            "timestamp": time.time(),
        },
    )


# Static files (for serving model artifacts, etc.)
if Path("static").exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")


# API Routes
api_prefix = f"/api/{settings.API_VERSION}"

app.include_router(
    health.router,
    prefix=api_prefix,
    tags=["Health"],
)

app.include_router(
    auth.router,
    prefix=f"{api_prefix}/auth",
    tags=["Authentication"],
)

app.include_router(
    datasets.router,
    prefix=f"{api_prefix}/datasets",
    tags=["Datasets"],
)

app.include_router(
    jobs.router,
    prefix=f"{api_prefix}/jobs",
    tags=["Jobs"],
)

app.include_router(
    models.router,
    prefix=f"{api_prefix}/models",
    tags=["Models"],
)


app.include_router(
    dataset_preprocessing.router,
    prefix=f"{api_prefix}/datasets",
    tags=["Dataset Preprocessing"],
)

app.include_router(
    analysis.router,
    prefix=f"{api_prefix}/analysis",
    tags=["Auto Analysis"],
)

app.include_router(
    workflow.router,
    prefix=f"{api_prefix}/workflow",
    tags=["ML Workflow"],
)

app.include_router(
    dna_discovery.router,
    prefix=f"{api_prefix}/dna-discovery",
    tags=["DNA Discovery"],
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "description": "AI-powered no-code platform for bioinformatics researchers",
        "environment": settings.ENVIRONMENT,
        "docs_url": f"{api_prefix}/docs" if settings.DEBUG else None,
        "health_check": f"{api_prefix}/health",
        "timestamp": time.time(),
    }


# API info endpoint
@app.get(f"{api_prefix}")
async def api_info():
    """API version information"""
    return {
        "api_version": settings.API_VERSION,
        "endpoints": {
            "health": f"{api_prefix}/health",
            "auth": f"{api_prefix}/auth",
            "datasets": f"{api_prefix}/datasets",
            "jobs": f"{api_prefix}/jobs",
            "models": f"{api_prefix}/models",
            "dna_discovery": f"{api_prefix}/dna-discovery",
        },
        "docs": f"{api_prefix}/docs" if settings.DEBUG else None,
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
