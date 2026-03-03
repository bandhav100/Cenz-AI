"""
Pydantic models for the PII Redaction Framework.
Defines request/response schemas for the API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class RedactionStrategy(str, Enum):
    MASK = "mask"
    TAG_REPLACE = "tag_replace"
    ANONYMIZE = "anonymize"
    HASH = "hash"


class InputFormat(str, Enum):
    TEXT = "text"
    PDF = "pdf"
    IMAGE = "image"


class DetectionSource(str, Enum):
    REGEX = "regex"
    NLP = "nlp"
    OCR = "ocr"
    LLM = "llm"


class PIIEntity(BaseModel):
    """Represents a single detected PII entity."""
    entity_type: str = Field(..., description="Type of PII (e.g., EMAIL, PHONE, NAME)")
    value: str = Field(..., description="The detected PII value")
    start: int = Field(..., description="Start character offset")
    end: int = Field(..., description="End character offset")
    confidence: float = Field(default=1.0, description="Detection confidence score (0-1)")
    source: str = Field(..., description="Detection engine source (regex, nlp, ocr, llm, or combined)")
    redacted_value: Optional[str] = Field(None, description="The redacted replacement value")


class RedactTextRequest(BaseModel):
    """Request schema for text redaction."""
    text: str = Field(..., description="Text to redact")
    strategy: RedactionStrategy = Field(default=RedactionStrategy.MASK, description="Redaction strategy")
    entity_types: Optional[List[str]] = Field(None, description="Specific entity types to detect")


class RedactTextResponse(BaseModel):
    """Response schema for text redaction."""
    original_text: str
    redacted_text: str
    entities_found: List[PIIEntity]
    total_entities: int
    processing_time_ms: float
    strategy_used: RedactionStrategy
    verification_passed: bool = True
    stats: Dict[str, Any] = {}


class FileUploadResponse(BaseModel):
    """Response schema for file upload redaction."""
    filename: str
    file_type: str
    original_size: int
    redacted_text: str
    entities_found: List[PIIEntity]
    total_entities: int
    processing_time_ms: float
    strategy_used: RedactionStrategy
    verification_passed: bool = True
    stats: Dict[str, Any] = {}


class BatchRedactRequest(BaseModel):
    """Request schema for batch text redaction."""
    texts: List[str]
    strategy: RedactionStrategy = RedactionStrategy.MASK
    entity_types: Optional[List[str]] = None


class BatchRedactResponse(BaseModel):
    """Response schema for batch text redaction."""
    results: List[RedactTextResponse]
    total_texts: int
    total_entities: int
    total_processing_time_ms: float


class AuditLogEntry(BaseModel):
    """Audit log entry for compliance tracking."""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    input_format: InputFormat
    entities_detected: int
    strategy_used: RedactionStrategy
    verification_passed: bool
    processing_time_ms: float
    entity_breakdown: Dict[str, int] = {}


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    engines: Dict[str, bool] = {}
    uptime_seconds: float = 0.0


class SystemStats(BaseModel):
    """System-wide statistics."""
    total_requests: int = 0
    total_entities_detected: int = 0
    total_texts_processed: int = 0
    total_files_processed: int = 0
    avg_processing_time_ms: float = 0.0
    entity_type_distribution: Dict[str, int] = {}
    strategy_usage: Dict[str, int] = {}
    recent_logs: List[AuditLogEntry] = []
