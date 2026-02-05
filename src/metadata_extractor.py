"""CSV-based metadata extraction from PDFs."""

import csv
import subprocess
import json
import logging
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime

from .config import settings
from .pdf_extractor import extract_text
from .claude_namer import _smart_truncate, _get_model_flag, MAX_CONTEXT_CHARS

logger = logging.getLogger(__name__)


EXTRACTION_PROMPT = '''Extract specific information from this document.

DOCUMENT TEXT:
---
{text}
---

FIELDS TO EXTRACT:
{fields}

For each field, find the corresponding value in the document. If a field cannot be found, use null.

Respond with a JSON object where keys are the exact field names and values are the extracted data:
{{"field1": "value1", "field2": "value2", ...}}

Rules:
- Use exact field names as keys (case-sensitive)
- Return null for fields not found in the document
- For dates, use YYYY-MM-DD format when possible
- For currency, include the number only (no $ or commas)
- Keep values concise but complete

Respond with ONLY the JSON object:'''


@dataclass
class ExtractionResult:
    """Result from metadata extraction for a single PDF."""

    file_path: str
    file_name: str
    extracted_data: Dict[str, Any]
    extraction_method: str
    confidence: float
    errors: List[str]


def load_template(template_path: Path) -> List[str]:
    """
    Load field names from a CSV template.

    The template should have column headers in the first row.
    These headers become the fields to extract from each document.
    """
    template_path = Path(template_path)

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    if template_path.suffix.lower() != '.csv':
        raise ValueError("Template must be a CSV file")

    with open(template_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        headers = next(reader, None)

    if not headers:
        raise ValueError("Template CSV has no headers")

    # Clean headers
    headers = [h.strip() for h in headers if h.strip()]

    if not headers:
        raise ValueError("Template CSV has no valid headers")

    logger.info(f"Loaded template with {len(headers)} fields: {headers}")
    return headers


def extract_metadata(
    text: str,
    fields: List[str],
    model: str = "sonnet"
) -> Dict[str, Any]:
    """
    Use Claude to extract specific fields from document text.

    Args:
        text: Document text to analyze
        fields: List of field names to extract
        model: Claude model to use

    Returns:
        Dictionary mapping field names to extracted values
    """
    # Get model-specific context limit
    max_chars = MAX_CONTEXT_CHARS.get(model, 50000)
    max_text_chars = max_chars - 2000  # Reserve more for prompt with field list

    # Smart truncate if needed
    text = _smart_truncate(text, max_text_chars)

    # Format fields list
    fields_text = "\n".join(f"- {field}" for field in fields)

    prompt = EXTRACTION_PROMPT.format(text=text, fields=fields_text)

    logger.debug(f"Extraction prompt length: {len(prompt)} chars")

    try:
        # Pass prompt via stdin to avoid CLI length limits on Windows
        result = subprocess.run(
            ["claude", "--print", "--model", _get_model_flag(model)],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=180,  # 3 minute timeout for extraction
            encoding='utf-8',
        )

        if result.returncode != 0:
            logger.error(f"Claude CLI error: {result.stderr}")
            return {field: None for field in fields}

        response = result.stdout.strip()

        # Parse JSON response
        try:
            # Try direct parse
            data = json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON in response
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    logger.warning("Could not parse extraction response")
                    return {field: None for field in fields}
            else:
                logger.warning("No JSON found in extraction response")
                return {field: None for field in fields}

        # Ensure all fields are present
        result_data = {}
        for field in fields:
            result_data[field] = data.get(field)

        return result_data

    except subprocess.TimeoutExpired:
        logger.error("Claude CLI timed out during extraction")
        return {field: None for field in fields}
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        return {field: None for field in fields}


def process_pdf_for_metadata(
    pdf_path: Path,
    fields: List[str],
    model: str = "sonnet"
) -> ExtractionResult:
    """
    Extract metadata from a single PDF.

    Args:
        pdf_path: Path to the PDF file
        fields: List of field names to extract
        model: Claude model to use

    Returns:
        ExtractionResult with extracted data
    """
    pdf_path = Path(pdf_path)
    errors = []

    logger.info(f"Extracting metadata from: {pdf_path.name}")

    # Extract text
    try:
        extraction = extract_text(pdf_path)
        if extraction.is_empty:
            errors.append("No text could be extracted")
            return ExtractionResult(
                file_path=str(pdf_path),
                file_name=pdf_path.name,
                extracted_data={field: None for field in fields},
                extraction_method="none",
                confidence=0.0,
                errors=errors,
            )
    except Exception as e:
        errors.append(f"Text extraction failed: {e}")
        return ExtractionResult(
            file_path=str(pdf_path),
            file_name=pdf_path.name,
            extracted_data={field: None for field in fields},
            extraction_method="error",
            confidence=0.0,
            errors=errors,
        )

    # Extract metadata
    extracted_data = extract_metadata(extraction.text, fields, model)

    # Calculate confidence based on how many fields were found
    found_count = sum(1 for v in extracted_data.values() if v is not None)
    confidence = found_count / len(fields) if fields else 0.0

    return ExtractionResult(
        file_path=str(pdf_path),
        file_name=pdf_path.name,
        extracted_data=extracted_data,
        extraction_method=extraction.method,
        confidence=confidence,
        errors=errors,
    )


def extract_to_csv(
    pdf_paths: List[Path],
    template_path: Path,
    output_path: Path,
    model: str = "sonnet",
    include_metadata_columns: bool = True,
) -> Path:
    """
    Extract metadata from multiple PDFs and save to CSV.

    Args:
        pdf_paths: List of PDF files to process
        template_path: Path to CSV template with column headers
        output_path: Path for output CSV
        model: Claude model to use
        include_metadata_columns: Add file_name, confidence, errors columns

    Returns:
        Path to the created CSV file
    """
    # Load template
    fields = load_template(template_path)

    # Prepare output columns
    if include_metadata_columns:
        output_columns = ['_file_name', '_file_path'] + fields + ['_confidence', '_extraction_method', '_errors']
    else:
        output_columns = fields

    # Process each PDF
    results = []
    for pdf_path in pdf_paths:
        result = process_pdf_for_metadata(pdf_path, fields, model)
        results.append(result)

    # Write output CSV
    output_path = Path(output_path)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=output_columns)
        writer.writeheader()

        for result in results:
            row = dict(result.extracted_data)

            if include_metadata_columns:
                row['_file_name'] = result.file_name
                row['_file_path'] = result.file_path
                row['_confidence'] = f"{result.confidence:.0%}"
                row['_extraction_method'] = result.extraction_method
                row['_errors'] = '; '.join(result.errors) if result.errors else ''

            writer.writerow(row)

    logger.info(f"Results written to: {output_path}")
    return output_path


def create_template(output_path: Path, fields: List[str]) -> Path:
    """
    Create a blank CSV template with specified fields.

    Args:
        output_path: Path for the template file
        fields: List of field names for columns

    Returns:
        Path to created template
    """
    output_path = Path(output_path)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(fields)

    logger.info(f"Template created: {output_path}")
    return output_path
