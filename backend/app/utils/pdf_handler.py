"""
PDF Content Extraction Handler.
Extracts text and embedded images from PDF files
using PyMuPDF (fitz) for downstream PII detection.
"""

from typing import List, Dict, Tuple, Optional
import os
import tempfile
import logging

logger = logging.getLogger(__name__)


class PDFHandler:
    """
    Handles PDF document ingestion, text extraction, and image extraction.
    """

    def __init__(self):
        self._available = False
        try:
            import fitz
            self._available = True
        except ImportError:
            logger.warning("PyMuPDF (fitz) not installed. PDF support disabled.")

    def is_available(self) -> bool:
        return self._available

    def extract_text(self, pdf_path: str) -> str:
        """
        Extract all text content from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text string
        """
        if not self._available:
            return ""

        import fitz

        try:
            doc = fitz.open(pdf_path)
            text_parts = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text_parts.append(page.get_text())
            doc.close()
            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            return ""

    def extract_text_by_page(self, pdf_path: str) -> List[Dict]:
        """
        Extract text from each page separately.

        Returns:
            List of dicts with page_number and text
        """
        if not self._available:
            return []

        import fitz

        try:
            doc = fitz.open(pdf_path)
            pages = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                pages.append({
                    "page_number": page_num + 1,
                    "text": page.get_text(),
                    "width": page.rect.width,
                    "height": page.rect.height
                })
            doc.close()
            return pages
        except Exception as e:
            logger.error(f"PDF page extraction failed: {e}")
            return []

    def extract_images(self, pdf_path: str, output_dir: str = None) -> List[str]:
        """
        Extract embedded images from a PDF file.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save extracted images

        Returns:
            List of paths to extracted image files
        """
        if not self._available:
            return []

        import fitz

        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="pii_pdf_images_")

        os.makedirs(output_dir, exist_ok=True)
        image_paths = []

        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images(full=True)

                for img_idx, img in enumerate(image_list):
                    xref = img[0]
                    try:
                        pix = fitz.Pixmap(doc, xref)
                        if pix.n - pix.alpha > 3:  # CMYK
                            pix = fitz.Pixmap(fitz.csRGB, pix)

                        img_path = os.path.join(
                            output_dir,
                            f"page{page_num + 1}_img{img_idx + 1}.png"
                        )
                        pix.save(img_path)
                        image_paths.append(img_path)
                    except Exception as e:
                        logger.warning(f"Failed to extract image {img_idx} from page {page_num}: {e}")

            doc.close()
        except Exception as e:
            logger.error(f"PDF image extraction failed: {e}")

        return image_paths

    def extract_text_from_bytes(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes in memory."""
        if not self._available:
            return ""

        import fitz

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text_parts = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text_parts.append(page.get_text())
            doc.close()
            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"PDF bytes extraction failed: {e}")
            return ""

    def get_metadata(self, pdf_path: str) -> Dict:
        """Extract PDF metadata."""
        if not self._available:
            return {}

        import fitz

        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            page_count = len(doc)
            doc.close()
            return {
                "page_count": page_count,
                **metadata
            }
        except Exception as e:
            logger.error(f"PDF metadata extraction failed: {e}")
            return {}
