"""
Module 2: PDF Redaction Engine
Handles both text-based and scanned PDFs.
- Text PDFs: PyMuPDF text spans → PII detection → draw_rect black fill
- Scanned PDFs: page→image→EasyOCR→PII→black rects→recompile PDF
Returns redacted PDF bytes + per-page audit JSON.
"""

import io
import logging
import time
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False
    logger.warning("PyMuPDF (fitz) not installed")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class PDFRedactor:
    """Redacts PII from PDF documents — text-based and scanned."""

    def __init__(self):
        self.image_redactor = None
        # Lazy import to avoid circular dependency
        try:
            from app.engines.image_redactor import ImageRedactor
            self.image_redactor = ImageRedactor()
        except Exception as e:
            logger.warning(f"ImageRedactor not available for scanned PDFs: {e}")

    def is_available(self) -> bool:
        return FITZ_AVAILABLE

    def redact_pdf(
        self,
        pdf_bytes: bytes,
        pii_pipeline_fn,
        strategy: str = "mask"
    ) -> Dict:
        """
        Full PDF redaction pipeline.

        Args:
            pdf_bytes: Raw PDF file bytes
            pii_pipeline_fn: Callable(text) -> List[dict] for PII detection
            strategy: Redaction strategy

        Returns:
            dict with redacted_pdf_bytes, per_page_audit, entities, etc.
        """
        start_time = time.time()

        if not FITZ_AVAILABLE:
            return {"error": "PyMuPDF not installed", "redacted_pdf_bytes": pdf_bytes}

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        all_entities = []
        per_page_audit = []
        full_text_parts = []

        for page_num in range(total_pages):
            page = doc[page_num]
            page_text = page.get_text("text")

            if len(page_text.strip()) > 20:
                # Text-based page
                page_result = self._redact_text_page(page, page_num, page_text, pii_pipeline_fn)
            else:
                # Scanned page — convert to image, OCR, redact
                page_result = self._redact_scanned_page(doc, page, page_num, pii_pipeline_fn)

            per_page_audit.append(page_result["audit"])
            all_entities.extend(page_result["entities"])
            full_text_parts.append(page_result.get("text", ""))

        # Save redacted PDF
        buf = io.BytesIO()
        doc.save(buf)
        doc.close()

        processing_time = (time.time() - start_time) * 1000

        return {
            "redacted_pdf_bytes": buf.getvalue(),
            "format": "pdf",
            "per_page_audit": per_page_audit,
            "entities_found": all_entities,
            "total_entities": len(all_entities),
            "total_pages": total_pages,
            "full_text": "\n\n".join(full_text_parts),
            "processing_time_ms": processing_time,
        }

    def _redact_text_page(self, page, page_num: int, page_text: str, pii_pipeline_fn) -> Dict:
        """Redact a text-based PDF page using text span coordinates."""
        entities = pii_pipeline_fn(page_text)
        page_audit = {
            "page": page_num + 1,
            "type": "text",
            "redactions": [],
        }

        for entity in entities:
            value = entity.get("value", "")
            if not value:
                continue

            # Search for the text on the page to get exact coordinates
            text_instances = page.search_for(value)
            for rect in text_instances:
                # PyMuPDF rect is already in PDF coordinate space (top-left origin)
                # Draw a black filled rectangle over the PII
                page.draw_rect(rect, color=(0, 0, 0), fill=(0, 0, 0))

                page_audit["redactions"].append({
                    "entity_type": entity.get("entity_type", "UNKNOWN"),
                    "value": value,
                    "confidence": entity.get("confidence", 0.0),
                    "coordinates": {
                        "x0": round(rect.x0, 2),
                        "y0": round(rect.y0, 2),
                        "x1": round(rect.x1, 2),
                        "y1": round(rect.y1, 2),
                    },
                })

        return {"audit": page_audit, "entities": entities, "text": page_text}

    def _redact_scanned_page(self, doc, page, page_num: int, pii_pipeline_fn) -> Dict:
        """Redact a scanned PDF page by converting to image, OCR, then redact."""
        page_audit = {
            "page": page_num + 1,
            "type": "scanned",
            "redactions": [],
        }

        if not self.image_redactor or not self.image_redactor.is_available():
            return {"audit": page_audit, "entities": [], "text": ""}

        # Convert page to image at 300 DPI for good OCR quality
        mat = fitz.Matrix(300 / 72, 300 / 72)  # scale factor for 300 DPI
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")

        # Use image redactor
        result = self.image_redactor.redact_image(img_bytes, pii_pipeline_fn)

        if result.get("redacted_image_bytes"):
            # Replace the page content with the redacted image
            redacted_img_bytes = result["redacted_image_bytes"]
            page_rect = page.rect

            # Clear page and insert redacted image
            # Remove existing content by covering with white rect first
            page.draw_rect(page_rect, color=(1, 1, 1), fill=(1, 1, 1))
            page.insert_image(page_rect, stream=redacted_img_bytes)

            # Scale coordinates back from 300 DPI to PDF points (72 DPI)
            scale = 72.0 / 300.0
            for audit_entry in result.get("audit_log", []):
                coords = audit_entry.get("pixel_coordinates", {}).get("bounding_rect", {})
                page_audit["redactions"].append({
                    "entity_type": audit_entry.get("entity_type", "UNKNOWN"),
                    "value": audit_entry.get("value", ""),
                    "confidence": audit_entry.get("confidence", 0.0),
                    "coordinates": {
                        "x0": round(coords.get("x0", 0) * scale, 2),
                        "y0": round(coords.get("y0", 0) * scale, 2),
                        "x1": round(coords.get("x1", 0) * scale, 2),
                        "y1": round(coords.get("y1", 0) * scale, 2),
                    },
                })

        return {
            "audit": page_audit,
            "entities": result.get("entities_found", []),
            "text": result.get("ocr_text", ""),
        }
