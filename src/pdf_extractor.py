"""PDF text extraction with automatic OCR fallback."""

import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import hashlib

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result of PDF text extraction."""

    text: str
    method: str  # "text", "ocr", or "hybrid"
    pages_processed: int
    total_pages: int
    content_hash: str  # For pattern matching

    @property
    def is_empty(self) -> bool:
        return len(self.text.strip()) == 0


def _compute_hash(text: str) -> str:
    """Compute a hash of extracted text for pattern matching."""
    # Use first 2000 chars for consistent hashing
    normalized = " ".join(text[:2000].lower().split())
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def _extract_text_pymupdf(pdf_path: Path, max_pages: int) -> tuple[str, int, int]:
    """Extract text directly using pymupdf."""
    import fitz  # pymupdf

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    pages_to_process = total_pages if max_pages == 0 else min(max_pages, total_pages)

    text_parts = []
    for page_num in range(pages_to_process):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

    doc.close()
    return "\n\n".join(text_parts), pages_to_process, total_pages


def _page_needs_ocr(page, min_text_threshold: int) -> bool:
    """Check if a page needs OCR (has little to no extractable text)."""
    text = page.get_text().strip()
    return len(text) < min_text_threshold


def _ocr_page(page, dpi: int, language: str) -> str:
    """OCR a single page using Tesseract."""
    import fitz  # pymupdf
    import pytesseract
    from PIL import Image
    import io

    # Render page to image
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)

    # Convert to PIL Image
    img_data = pix.tobytes("png")
    image = Image.open(io.BytesIO(img_data))

    # Run OCR
    text = pytesseract.image_to_string(image, lang=language)
    return text


def _check_tesseract_available() -> bool:
    """Check if Tesseract is installed and available."""
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def extract_text(pdf_path: Path) -> ExtractionResult:
    """
    Extract text from a PDF file.

    Automatically detects whether pages need OCR and uses the appropriate method.
    Respects speed_mode settings for DPI and page limits.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        ExtractionResult with extracted text and metadata
    """
    import fitz  # pymupdf

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    max_pages = settings.get_max_pages()
    dpi = settings.get_ocr_dpi()
    min_text = settings.min_text_threshold
    ocr_lang = settings.ocr_language

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    pages_to_process = total_pages if max_pages == 0 else min(max_pages, total_pages)

    logger.info(f"Processing {pdf_path.name}: {pages_to_process}/{total_pages} pages, mode={settings.speed_mode}")

    text_parts = []
    methods_used = set()
    tesseract_available = None  # Lazy check

    for page_num in range(pages_to_process):
        page = doc[page_num]

        # Try direct text extraction first
        direct_text = page.get_text().strip()

        if len(direct_text) >= min_text:
            # Page has sufficient text, use it directly
            text_parts.append(f"--- Page {page_num + 1} ---\n{direct_text}")
            methods_used.add("text")
            logger.debug(f"Page {page_num + 1}: Direct text extraction ({len(direct_text)} chars)")
        else:
            # Page needs OCR
            if tesseract_available is None:
                tesseract_available = _check_tesseract_available()

            if tesseract_available:
                try:
                    ocr_text = _ocr_page(page, dpi, ocr_lang)
                    if ocr_text.strip():
                        text_parts.append(f"--- Page {page_num + 1} (OCR) ---\n{ocr_text}")
                        methods_used.add("ocr")
                        logger.debug(f"Page {page_num + 1}: OCR extraction ({len(ocr_text)} chars)")
                    else:
                        logger.debug(f"Page {page_num + 1}: OCR returned empty result")
                except Exception as e:
                    logger.warning(f"Page {page_num + 1}: OCR failed - {e}")
                    # Fall back to whatever text we got
                    if direct_text:
                        text_parts.append(f"--- Page {page_num + 1} ---\n{direct_text}")
                        methods_used.add("text")
            else:
                # No Tesseract, use whatever text is available
                if direct_text:
                    text_parts.append(f"--- Page {page_num + 1} ---\n{direct_text}")
                    methods_used.add("text")
                else:
                    logger.warning(f"Page {page_num + 1}: No text and Tesseract unavailable")

    doc.close()

    full_text = "\n\n".join(text_parts)

    # Determine method used
    if methods_used == {"text"}:
        method = "text"
    elif methods_used == {"ocr"}:
        method = "ocr"
    elif methods_used:
        method = "hybrid"
    else:
        method = "none"

    result = ExtractionResult(
        text=full_text,
        method=method,
        pages_processed=pages_to_process,
        total_pages=total_pages,
        content_hash=_compute_hash(full_text) if full_text else "",
    )

    logger.info(f"Extracted {len(full_text)} chars via {method} method")
    return result


def get_pdf_info(pdf_path: Path) -> dict:
    """Get basic PDF metadata without full extraction."""
    import fitz

    pdf_path = Path(pdf_path)
    doc = fitz.open(pdf_path)

    info = {
        "path": str(pdf_path),
        "filename": pdf_path.name,
        "pages": len(doc),
        "metadata": doc.metadata,
    }

    doc.close()
    return info
