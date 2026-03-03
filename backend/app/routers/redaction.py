"""
API Router for PII Redaction endpoints.
All CPU-heavy operations (EasyOCR, Whisper, video) run in a thread pool
via run_in_executor so the FastAPI event loop is never blocked.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional
import time
import logging
import os

from app.models.schemas import (
    RedactTextRequest,
    RedactTextResponse,
    FileUploadResponse,
    BatchRedactRequest,
    BatchRedactResponse,
    HealthResponse,
    RedactionStrategy,
)
from app.orchestrator import RedactionOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["PII Redaction"])

# Singleton orchestrator
orchestrator = RedactionOrchestrator()

# Thread pool - keeps heavy CPU work off the event loop
# Use min(4, cpu_count) workers; image/audio/video are I/O + CPU bound
_executor = ThreadPoolExecutor(max_workers=4)


async def run_blocking(fn, *args, **kwargs):
    """Run a blocking function in the thread pool without blocking the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor,
        lambda: fn(*args, **kwargs)
    )


# ──────────────────────────────────────────────────────
# HEALTH & INFO
# ──────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check — always fast, never blocked by heavy ops."""
    engines = orchestrator.get_engine_status()
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        engines=engines,
        uptime_seconds=0
    )


@router.get("/strategies")
async def get_strategies():
    from app.engines.redaction_engine import RedactionEngine
    return {"strategies": RedactionEngine.get_strategies()}


@router.get("/entity-types")
async def get_entity_types():
    regex_types = orchestrator.regex_engine.get_supported_types()
    nlp_types = orchestrator.nlp_engine.get_supported_types() if orchestrator.nlp_engine.is_available() else []
    all_types = sorted(set(regex_types + nlp_types))
    return {"entity_types": all_types, "regex_types": regex_types, "nlp_types": nlp_types, "total": len(all_types)}


@router.get("/stats")
async def get_stats():
    return orchestrator.get_stats()


@router.get("/engines")
async def get_engines():
    return orchestrator.get_engine_status()


# ──────────────────────────────────────────────────────
# TEXT REDACTION — fast, no OCR/Whisper
# ──────────────────────────────────────────────────────

@router.post("/redact/text", response_model=RedactTextResponse)
async def redact_text(request: RedactTextRequest):
    """Redact PII from plain text. Runs inline (fast, regex+NLP only)."""
    try:
        result = await run_blocking(
            orchestrator.redact_text,
            request.text,
            request.strategy.value,
            request.entity_types,
        )
        return RedactTextResponse(**result)
    except Exception as e:
        logger.error(f"Text redaction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────
# FILE UPLOAD (legacy — text extract)
# ──────────────────────────────────────────────────────

@router.post("/redact/file", response_model=FileUploadResponse)
async def redact_file(
    file: UploadFile = File(...),
    strategy: RedactionStrategy = Form(default=RedactionStrategy.MASK)
):
    content_type = file.content_type or "application/octet-stream"
    filename = file.filename or "upload"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    ext_map = {"txt": "text/plain", "csv": "text/csv", "json": "application/json",
               "pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}
    if content_type == "application/octet-stream" and ext in ext_map:
        content_type = ext_map[ext]
    try:
        file_bytes = await file.read()
        result = await run_blocking(
            orchestrator.redact_file_bytes,
            file_bytes, filename, content_type, strategy.value
        )
        return FileUploadResponse(**result)
    except Exception as e:
        logger.error(f"File redaction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────
# IMAGE REDACTION — heavy: EasyOCR → thread pool
# ──────────────────────────────────────────────────────

@router.post("/redact/image")
async def redact_image(
    file: UploadFile = File(...),
    strategy: RedactionStrategy = Form(default=RedactionStrategy.MASK)
):
    """Redact PII from image. EasyOCR runs in thread pool (non-blocking)."""
    filename = file.filename or "image.png"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in {"jpg", "jpeg", "png", "webp"}:
        raise HTTPException(status_code=400, detail=f"Unsupported image format: {ext}")

    try:
        image_bytes = await file.read()
        # ← run_in_executor keeps EasyOCR off the event loop
        result = await run_blocking(orchestrator.redact_image, image_bytes, filename, strategy.value)
        result.pop("redacted_image_bytes", None)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Image redaction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────
# PDF REDACTION — heavy: PyMuPDF + optional EasyOCR
# ──────────────────────────────────────────────────────

@router.post("/redact/pdf")
async def redact_pdf(
    file: UploadFile = File(...),
    strategy: RedactionStrategy = Form(default=RedactionStrategy.MASK)
):
    """Redact PII from PDF. Runs in thread pool (non-blocking)."""
    filename = file.filename or "document.pdf"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext != "pdf":
        raise HTTPException(status_code=400, detail="Only PDF files accepted")

    try:
        pdf_bytes = await file.read()
        result = await run_blocking(orchestrator.redact_pdf, pdf_bytes, filename, strategy.value)
        result.pop("redacted_pdf_bytes", None)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"PDF redaction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────
# AUDIO REDACTION — heavy: Whisper transcription
# ──────────────────────────────────────────────────────

@router.post("/redact/audio")
async def redact_audio(
    file: UploadFile = File(...),
    strategy: RedactionStrategy = Form(default=RedactionStrategy.MASK)
):
    """Redact PII from audio. Whisper runs in thread pool (non-blocking)."""
    filename = file.filename or "audio.mp3"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in {"mp3", "wav", "m4a", "ogg", "flac"}:
        raise HTTPException(status_code=400, detail=f"Unsupported audio format: {ext}")

    try:
        audio_bytes = await file.read()
        result = await run_blocking(orchestrator.redact_audio, audio_bytes, filename, strategy.value)
        result.pop("redacted_audio_bytes", None)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Audio redaction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────
# VIDEO REDACTION — heavy: frame OCR + face blur + Whisper
# ──────────────────────────────────────────────────────

@router.post("/redact/video")
async def redact_video(
    file: UploadFile = File(...),
    strategy: RedactionStrategy = Form(default=RedactionStrategy.MASK)
):
    """Redact PII from video. All heavy work runs in thread pool (non-blocking)."""
    filename = file.filename or "video.mp4"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in {"mp4", "mov", "avi", "mkv", "webm"}:
        raise HTTPException(status_code=400, detail=f"Unsupported video format: {ext}")

    try:
        video_bytes = await file.read()
        result = await run_blocking(orchestrator.redact_video, video_bytes, filename, strategy.value)
        result.pop("redacted_video_bytes", None)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Video redaction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────
# BATCH REDACTION
# ──────────────────────────────────────────────────────

@router.post("/redact/batch", response_model=BatchRedactResponse)
async def batch_redact(request: BatchRedactRequest):
    if len(request.texts) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 texts per batch")
    try:
        result = await run_blocking(
            orchestrator.batch_redact,
            request.texts, request.strategy.value, request.entity_types
        )
        return BatchRedactResponse(**result)
    except Exception as e:
        logger.error(f"Batch redaction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────
# FILE DOWNLOAD (Module 5)
# ──────────────────────────────────────────────────────

@router.get("/download/{job_id}")
async def download_file(job_id: str):
    """
    Stream a redacted file by job ID.
    Fast — just reads pre-saved file from disk, no processing.
    """
    job = orchestrator.download_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or expired. Please re-upload and redact.")

    filepath = orchestrator.download_manager.get_filepath(job_id)
    if not filepath:
        raise HTTPException(status_code=404, detail="File not found on disk.")

    return FileResponse(
        path=filepath,
        filename=job["filename"],
        media_type=job["content_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{job["filename"]}"',
            "X-Job-Id": job_id,
        }
    )


@router.get("/download/{job_id}/info")
async def download_info(job_id: str):
    """Get metadata about a download job."""
    job = orchestrator.download_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or expired")
    return {
        "job_id": job_id,
        "filename": job["filename"],
        "content_type": job["content_type"],
        "file_size": job["file_size"],
        "entity_count": job["entity_count"],
        "processing_time_ms": job["processing_time_ms"],
        "audit_log": job.get("audit_log", []),
    }
