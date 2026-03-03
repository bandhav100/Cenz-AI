"""
OCR-based PII Detection Engine.
Extracts text from images and scanned documents using EasyOCR/Tesseract,
then feeds extracted text through regex and NLP engines.
"""

from typing import List, Dict, Optional, Tuple
import logging
import os

logger = logging.getLogger(__name__)


class OCREngine:
    """
    OCR engine for extracting text from images.
    Supports EasyOCR (primary) and Tesseract (fallback).
    """

    def __init__(self, use_easyocr: bool = True, languages: List[str] = None):
        self.use_easyocr = use_easyocr
        self.languages = languages or ["en"]
        self.reader = None
        self._loaded = False

    def load(self):
        """Load the OCR engine."""
        if self._loaded:
            return

        if self.use_easyocr:
            try:
                import easyocr
                self.reader = easyocr.Reader(self.languages, gpu=False)
                self._loaded = True
                logger.info("EasyOCR engine loaded successfully")
                return
            except ImportError:
                logger.warning("EasyOCR not installed, falling back to Tesseract")
            except Exception as e:
                logger.warning(f"EasyOCR load failed: {e}, falling back to Tesseract")

        # Fallback to Tesseract
        try:
            import pytesseract
            from PIL import Image
            # Test that tesseract binary is available
            pytesseract.get_tesseract_version()
            self.use_easyocr = False
            self._loaded = True
            logger.info("Tesseract OCR engine loaded successfully")
        except Exception as e:
            logger.error(f"No OCR engine available: {e}")
            self._loaded = False

    def is_available(self) -> bool:
        """Check if OCR engine is loaded and available."""
        return self._loaded

    def extract_text(self, image_path: str) -> str:
        """
        Extract text from an image file.

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text string
        """
        if not self.is_available():
            self.load()
            if not self.is_available():
                logger.warning("OCR engine not available")
                return ""

        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return ""

        try:
            if self.use_easyocr:
                return self._extract_with_easyocr(image_path)
            else:
                return self._extract_with_tesseract(image_path)
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""

    def extract_text_with_positions(self, image_path: str) -> List[Dict]:
        """
        Extract text with bounding box positions from an image.

        Args:
            image_path: Path to the image file

        Returns:
            List of dicts with text, bbox, and confidence
        """
        if not self.is_available():
            self.load()
            if not self.is_available():
                return []

        if not os.path.exists(image_path):
            return []

        try:
            if self.use_easyocr:
                return self._extract_positions_easyocr(image_path)
            else:
                return self._extract_positions_tesseract(image_path)
        except Exception as e:
            logger.error(f"OCR position extraction failed: {e}")
            return []

    def _extract_with_easyocr(self, image_path: str) -> str:
        """Extract text using EasyOCR."""
        results = self.reader.readtext(image_path)
        text_parts = [result[1] for result in results]
        return " ".join(text_parts)

    def _extract_with_tesseract(self, image_path: str) -> str:
        """Extract text using Tesseract OCR."""
        import pytesseract
        from PIL import Image
        image = Image.open(image_path)
        # Convert to RGB to handle CMYK, RGBA, palette modes and avoid JPEG corruption
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        text = pytesseract.image_to_string(image)
        return text

    def _extract_positions_easyocr(self, image_path: str) -> List[Dict]:
        """Extract text with positions using EasyOCR."""
        results = self.reader.readtext(image_path)
        positions = []
        for bbox, text, confidence in results:
            positions.append({
                "text": text,
                "bbox": {
                    "top_left": bbox[0],
                    "top_right": bbox[1],
                    "bottom_right": bbox[2],
                    "bottom_left": bbox[3]
                },
                "confidence": float(confidence)
            })
        return positions

    def _extract_positions_tesseract(self, image_path: str) -> List[Dict]:
        """Extract text with positions using Tesseract."""
        import pytesseract
        from PIL import Image
        image = Image.open(image_path)
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        positions = []
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            if text:
                positions.append({
                    "text": text,
                    "bbox": {
                        "x": data['left'][i],
                        "y": data['top'][i],
                        "width": data['width'][i],
                        "height": data['height'][i]
                    },
                    "confidence": float(data['conf'][i]) / 100.0
                })
        return positions

    def extract_text_from_bytes(self, image_bytes: bytes) -> str:
        """Extract text from image bytes."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        try:
            result = self.extract_text(tmp_path)
        finally:
            os.unlink(tmp_path)
        return result

    def get_supported_formats(self) -> List[str]:
        """Return list of supported image formats."""
        return ["png", "jpg", "jpeg", "bmp", "tiff", "webp"]
