"""
Module 1: Image Redaction Engine
Accepts JPG/PNG/WEBP, runs EasyOCR for text+bounding boxes,
detects PII via pipeline, draws black rectangles over PII regions.
Returns redacted image + JSON audit log.
"""

import io
import logging
import time
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("Pillow not installed")

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not installed")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logger.warning("EasyOCR not installed")


class ImageRedactor:
    """Redacts PII from images using OCR + bounding box overlay."""

    def __init__(self):
        self.ocr_reader = None
        if EASYOCR_AVAILABLE:
            try:
                self.ocr_reader = easyocr.Reader(["en"], gpu=False)
                logger.info("EasyOCR reader initialized for ImageRedactor")
            except Exception as e:
                logger.error(f"EasyOCR init failed: {e}")

    def is_available(self) -> bool:
        return PIL_AVAILABLE and (EASYOCR_AVAILABLE or CV2_AVAILABLE)

    def redact_image(
        self,
        image_bytes: bytes,
        pii_pipeline_fn,
        strategy: str = "mask"
    ) -> Dict:
        """
        Full image redaction pipeline.

        Args:
            image_bytes: Raw image file bytes
            pii_pipeline_fn: Callable(text) -> List[dict] that returns PII entities
            strategy: Redaction strategy

        Returns:
            dict with redacted_image_bytes, audit_log, entities, etc.
        """
        start_time = time.time()

        # Load image
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_width, img_height = img.size

        # Run OCR with bounding boxes
        ocr_results = self._run_ocr(image_bytes)
        if not ocr_results:
            # No text found
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return {
                "redacted_image_bytes": buf.getvalue(),
                "format": "png",
                "audit_log": [],
                "entities_found": [],
                "total_entities": 0,
                "ocr_text": "",
                "processing_time_ms": (time.time() - start_time) * 1000,
                "image_dimensions": {"width": img_width, "height": img_height},
            }

        # Build full text from OCR for PII detection
        full_text_parts = []
        char_to_box_map = []  # Maps character offset -> OCR result index

        for idx, (bbox, text, conf) in enumerate(ocr_results):
            start_offset = len(" ".join(full_text_parts))
            if full_text_parts:
                start_offset += 1  # account for space separator
            full_text_parts.append(text)
            end_offset = start_offset + len(text)
            char_to_box_map.append({
                "idx": idx,
                "bbox": bbox,
                "text": text,
                "conf": conf,
                "start": start_offset,
                "end": end_offset,
            })

        full_text = " ".join(full_text_parts)

        # Run PII detection on extracted text
        pii_entities = pii_pipeline_fn(full_text)

        # Map PII entities back to bounding boxes
        redaction_regions = []
        for entity in pii_entities:
            ent_start = entity.get("start", 0)
            ent_end = entity.get("end", 0)
            ent_value = entity.get("value", "")

            # Find overlapping OCR boxes
            for box_info in char_to_box_map:
                if ent_start < box_info["end"] and ent_end > box_info["start"]:
                    redaction_regions.append({
                        "bbox": box_info["bbox"],
                        "entity_type": entity.get("entity_type", "UNKNOWN"),
                        "value": ent_value,
                        "confidence": entity.get("confidence", 0.0),
                        "source": entity.get("source", "pipeline"),
                        "ocr_text": box_info["text"],
                        "ocr_confidence": box_info["conf"],
                    })

        # Draw black rectangles over PII regions
        draw = ImageDraw.Draw(img)
        audit_log = []

        for region in redaction_regions:
            bbox = region["bbox"]
            # EasyOCR returns [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] polygon
            polygon = self._bbox_to_polygon(bbox)
            draw.polygon(polygon, fill="black")

            audit_log.append({
                "entity_type": region["entity_type"],
                "value": region["value"],
                "confidence": region["confidence"],
                "source": region["source"],
                "pixel_coordinates": {
                    "polygon": [[int(p[0]), int(p[1])] for p in bbox],
                    "bounding_rect": self._polygon_to_rect(bbox),
                },
                "ocr_text": region["ocr_text"],
                "ocr_confidence": float(region["ocr_confidence"]),
            })

        # Save redacted image
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        processing_time = (time.time() - start_time) * 1000

        return {
            "redacted_image_bytes": buf.getvalue(),
            "format": "png",
            "audit_log": audit_log,
            "entities_found": pii_entities,
            "total_entities": len(audit_log),
            "ocr_text": full_text,
            "processing_time_ms": processing_time,
            "image_dimensions": {"width": img_width, "height": img_height},
        }

    def _run_ocr(self, image_bytes: bytes) -> List[Tuple]:
        """Run EasyOCR or Tesseract, returns list of (bbox, text, confidence)."""
        if self.ocr_reader:
            try:
                np_arr = np.frombuffer(image_bytes, np.uint8)
                img_cv = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                results = self.ocr_reader.readtext(img_cv)
                return results  # [(bbox, text, conf), ...]
            except Exception as e:
                logger.error(f"EasyOCR failed: {e}")

        # Fallback: Tesseract with bounding boxes
        try:
            import pytesseract
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            results = []
            for i in range(len(data["text"])):
                text = data["text"][i].strip()
                if not text:
                    continue
                x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                conf = float(data["conf"][i]) / 100.0 if data["conf"][i] != -1 else 0.5
                bbox = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
                results.append((bbox, text, conf))
            return results
        except Exception as e:
            logger.error(f"Tesseract fallback failed: {e}")
            return []

    def _bbox_to_polygon(self, bbox) -> List[Tuple[int, int]]:
        """Convert EasyOCR bbox to PIL polygon coordinates."""
        return [(int(p[0]), int(p[1])) for p in bbox]

    def _polygon_to_rect(self, bbox) -> Dict:
        """Convert polygon to bounding rectangle."""
        xs = [int(p[0]) for p in bbox]
        ys = [int(p[1]) for p in bbox]
        return {"x0": min(xs), "y0": min(ys), "x1": max(xs), "y1": max(ys)}
