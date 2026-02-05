"""PDF splitting with document boundary detection."""

import logging
import subprocess
import json
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class PageInfo:
    """Information about a single PDF page."""
    page_num: int  # 0-indexed
    text: str
    doc_type: Optional[str] = None
    confidence: float = 0.0


@dataclass
class DocumentSegment:
    """A segment of pages that form a single document."""
    start_page: int  # 0-indexed
    end_page: int    # 0-indexed, inclusive
    doc_type: str
    suggested_name: str
    confidence: float

    @property
    def page_count(self) -> int:
        return self.end_page - self.start_page + 1

    def __str__(self) -> str:
        if self.start_page == self.end_page:
            return f"Page {self.start_page + 1}: {self.suggested_name}"
        return f"Pages {self.start_page + 1}-{self.end_page + 1}: {self.suggested_name}"


BOUNDARY_DETECTION_PROMPT = '''Analyze these PDF pages and identify document boundaries.

Each page's text is provided below. Determine if consecutive pages belong to the same document or are different documents that were scanned together.

PAGES:
{pages_text}

Respond with a JSON array where each object represents a distinct document found:
{{
  "documents": [
    {{
      "start_page": 1,
      "end_page": 2,
      "doc_type": "Mortgage Statement",
      "suggested_name": "LoanDepot_Mortgage_Statement",
      "confidence": 0.95
    }},
    {{
      "start_page": 3,
      "end_page": 3,
      "doc_type": "Utility Bill",
      "suggested_name": "Electric_Bill",
      "confidence": 0.90
    }}
  ]
}}

Rules:
- Page numbers are 1-indexed in your response
- Group consecutive pages that clearly belong together (same header, continuing content)
- Separate pages with different document types, headers, or senders
- Use Title_Case_With_Underscores for suggested_name
- Be conservative - only split when clearly different documents

Respond with ONLY the JSON object:'''


def extract_pages_text(pdf_path: Path, max_chars_per_page: int = 1500) -> List[PageInfo]:
    """Extract text from each page of a PDF."""
    import fitz

    doc = fitz.open(pdf_path)
    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text().strip()

        # Truncate if too long
        if len(text) > max_chars_per_page:
            text = text[:max_chars_per_page] + "..."

        pages.append(PageInfo(
            page_num=page_num,
            text=text if text else "[No extractable text - may need OCR]"
        ))

    doc.close()
    return pages


def detect_boundaries_with_claude(
    pages: List[PageInfo],
    model: str = "sonnet"
) -> List[DocumentSegment]:
    """Use Claude to detect document boundaries."""

    # Format pages for the prompt
    pages_text = ""
    for p in pages:
        pages_text += f"\n--- PAGE {p.page_num + 1} ---\n{p.text}\n"

    prompt = BOUNDARY_DETECTION_PROMPT.format(pages_text=pages_text)

    logger.info(f"Analyzing {len(pages)} pages for document boundaries...")

    try:
        result = subprocess.run(
            ["claude", "--print", "--model", model, prompt],
            capture_output=True,
            text=True,
            timeout=120,
            encoding='utf-8',
        )

        if result.returncode != 0:
            logger.error(f"Claude CLI error: {result.stderr}")
            return []

        response = result.stdout.strip()

        # Parse JSON response
        json_match = re.search(r'\{[\s\S]*"documents"[\s\S]*\}', response)
        if json_match:
            data = json.loads(json_match.group(0))
            segments = []
            for doc in data.get("documents", []):
                segments.append(DocumentSegment(
                    start_page=doc["start_page"] - 1,  # Convert to 0-indexed
                    end_page=doc["end_page"] - 1,
                    doc_type=doc.get("doc_type", "Unknown"),
                    suggested_name=doc.get("suggested_name", "Document"),
                    confidence=doc.get("confidence", 0.5),
                ))
            return segments

    except Exception as e:
        logger.error(f"Error detecting boundaries: {e}")

    return []


def split_pdf(
    pdf_path: Path,
    segments: List[DocumentSegment],
    output_dir: Optional[Path] = None
) -> List[Path]:
    """Split a PDF into multiple files based on segments."""
    import fitz

    if output_dir is None:
        output_dir = pdf_path.parent

    doc = fitz.open(pdf_path)
    created_files = []

    for i, segment in enumerate(segments):
        # Create new PDF with just these pages
        new_doc = fitz.open()

        for page_num in range(segment.start_page, segment.end_page + 1):
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

        # Generate output filename
        base_name = f"split_{i+1}_{segment.suggested_name}"
        output_path = output_dir / f"{base_name}.pdf"

        # Handle duplicates
        counter = 1
        while output_path.exists():
            output_path = output_dir / f"{base_name}_{counter}.pdf"
            counter += 1

        new_doc.save(str(output_path))
        new_doc.close()
        created_files.append(output_path)

        logger.info(f"Created: {output_path.name}")

    doc.close()
    return created_files


def analyze_pdf_for_split(
    pdf_path: Path,
    model: str = "sonnet"
) -> Tuple[List[PageInfo], List[DocumentSegment]]:
    """
    Analyze a PDF and return page info and detected document segments.

    Returns:
        Tuple of (pages, segments)
    """
    pages = extract_pages_text(pdf_path)

    if len(pages) <= 1:
        # Single page, no split needed
        return pages, []

    segments = detect_boundaries_with_claude(pages, model)

    # If only one segment covering all pages, no split needed
    if len(segments) <= 1:
        return pages, []

    return pages, segments


def interactive_split(
    pdf_path: Path,
    model: str = "sonnet"
) -> List[Path]:
    """
    Interactively analyze and split a PDF.

    Returns list of resulting PDF paths (may be just the original if no split).
    """
    logger = logging.getLogger(__name__)

    logger.info(f"\nAnalyzing: {pdf_path.name}")

    pages, segments = analyze_pdf_for_split(pdf_path, model)

    if not segments:
        logger.info("Single document detected, no split needed.")
        return [pdf_path]

    # Show detected segments
    logger.info(f"\nDetected {len(segments)} document(s) in this PDF:")
    logger.info("-" * 50)
    for i, seg in enumerate(segments, 1):
        logger.info(f"  {i}. {seg}")
        logger.info(f"      Type: {seg.doc_type} (confidence: {seg.confidence:.0%})")
    logger.info("-" * 50)

    # Prompt for action
    print(f"\nSplit '{pdf_path.name}' into {len(segments)} documents?")
    print("  [Y] Yes, split as shown")
    print("  [N] No, keep as single document")
    print("  [P] Split by individual pages (one PDF per page)")
    print("  [S] Skip this file")

    while True:
        choice = input("\nChoice [Y/N/P/S]: ").strip().upper()

        if choice == 'Y':
            # Split as detected
            logger.info("\nSplitting PDF...")
            new_files = split_pdf(pdf_path, segments)

            # Optionally remove original
            print(f"\nCreated {len(new_files)} files. Delete original '{pdf_path.name}'?")
            if input("[y/N]: ").strip().lower() == 'y':
                pdf_path.unlink()
                logger.info(f"Deleted: {pdf_path.name}")

            return new_files

        elif choice == 'N':
            logger.info("Keeping as single document.")
            return [pdf_path]

        elif choice == 'P':
            # Split every page
            logger.info("\nSplitting into individual pages...")
            page_segments = [
                DocumentSegment(
                    start_page=i,
                    end_page=i,
                    doc_type="Page",
                    suggested_name=f"page_{i+1}",
                    confidence=1.0
                )
                for i in range(len(pages))
            ]
            new_files = split_pdf(pdf_path, page_segments)

            print(f"\nCreated {len(new_files)} files. Delete original?")
            if input("[y/N]: ").strip().lower() == 'y':
                pdf_path.unlink()
                logger.info(f"Deleted: {pdf_path.name}")

            return new_files

        elif choice == 'S':
            logger.info("Skipping this file.")
            return []

        else:
            print("Invalid choice. Please enter Y, N, P, or S.")
