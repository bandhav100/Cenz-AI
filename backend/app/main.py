"""
AI PII Redactor - FastAPI Application
Multi-Modal Privacy Preservation Framework

Main application entry point with CORS, logging, and route registration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import time

from app.routers import redaction

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Track startup time
START_TIME = time.time()

# Create FastAPI app
app = FastAPI(
    title="AI PII Redactor",
    description="""
    ## Multi-Modal Privacy Preservation Framework

    An AI-driven PII redaction system that combines:
    - **Regex Pattern Engine** for structured identifiers
    - **NLP (spaCy NER)** for contextual entity detection
    - **OCR Pipeline** for image/PDF processing
    - **Multiple Redaction Strategies**: masking, tagging, anonymization, hashing

    ### Supported Formats
    - Plain text
    - PDF documents
    - Images (PNG, JPG)
    - CSV & JSON datasets

    ### API Endpoints
    - `/api/v1/redact/text` — Redact PII from text
    - `/api/v1/redact/file` — Redact PII from uploaded files
    - `/api/v1/redact/batch` — Batch text redaction
    - `/api/v1/strategies` — List redaction strategies
    - `/api/v1/entity-types` — List detected entity types
    - `/api/v1/stats` — Processing statistics
    - `/api/v1/health` — Health check
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Type", "Content-Length"],
)

# Register routers
app.include_router(redaction.router)


@app.get("/")
async def root():
    """Root endpoint with system info."""
    uptime = time.time() - START_TIME
    return {
        "name": "AI PII Redactor",
        "version": "1.0.0",
        "description": "Multi-Modal Privacy Preservation Framework",
        "uptime_seconds": round(uptime, 2),
        "docs": "/docs",
        "api_base": "/api/v1"
    }


@app.on_event("startup")
async def startup_event():
    logger.info("🛡️  AI PII Redactor starting up...")
    logger.info("📚 API documentation available at /docs")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛡️  AI PII Redactor shutting down...")
