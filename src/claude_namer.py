"""Claude Code CLI integration for intelligent file naming."""

import subprocess
import json
import logging
import re
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

from .config import settings, ModelType

logger = logging.getLogger(__name__)

# Context limits (conservative estimates in characters)
# Claude models support ~200k tokens, but we use conservative limits
MAX_CONTEXT_CHARS = {
    "haiku": 50000,    # ~12k tokens, fast model
    "sonnet": 100000,  # ~25k tokens, balanced
    "opus": 150000,    # ~37k tokens, most capable
}

# Prompt template for naming suggestions
NAMING_PROMPT = '''Analyze this document text and suggest a filename.

DOCUMENT TEXT (extracted from PDF):
---
{text}
---

Based on the document content, provide a JSON response with:
1. "date": The most relevant date in YYYY-MM-DD format (document date, invoice date, statement date, etc.). Use null if no date found.
2. "description": A concise description (2-5 words, use underscores between words). Be specific: "Electric_Bill_January" not just "Bill".
3. "confidence": Your confidence in this naming (0.0 to 1.0).
4. "reasoning": Brief explanation of your choice (1 sentence).

Rules:
- Description should identify the document type and key details
- Use Title_Case_With_Underscores for description
- Avoid generic names like "Document" or "Scan"
- Include relevant identifiers when present (company name, account type, etc.)

Respond with ONLY the JSON object, no other text:
{{"date": "YYYY-MM-DD", "description": "Description_Here", "confidence": 0.95, "reasoning": "explanation"}}'''


@dataclass
class NamingResult:
    """Result from Claude naming suggestion."""

    date: Optional[str]
    description: str
    confidence: float
    reasoning: str
    model_used: str
    raw_response: str

    def get_filename(self, extension: str = ".pdf") -> str:
        """Generate the final filename."""
        if self.date:
            return f"{self.date}_{self.description}{extension}"
        else:
            # Use today's date as fallback with marker
            today = datetime.now().strftime("%Y-%m-%d")
            return f"{today}_UNDATED_{self.description}{extension}"


def _clean_filename(name: str) -> str:
    """Remove invalid filename characters."""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    # Collapse multiple underscores
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    return name


def _smart_truncate(text: str, max_chars: int) -> str:
    """
    Intelligently truncate text to fit within context limits.

    Strategy:
    - Keep first 60% (headers, document type, dates usually at top)
    - Keep last 20% (signatures, totals, conclusions)
    - Sample from middle 20% (supporting content)
    """
    if len(text) <= max_chars:
        return text

    # Calculate section sizes
    first_size = int(max_chars * 0.60)
    last_size = int(max_chars * 0.20)
    middle_size = max_chars - first_size - last_size - 100  # 100 chars for markers

    first_part = text[:first_size]
    last_part = text[-last_size:]

    # Get middle sample
    middle_start = len(text) // 3
    middle_part = text[middle_start:middle_start + middle_size]

    truncated = (
        f"{first_part}\n\n"
        f"[... {len(text) - max_chars:,} characters truncated ...]\n\n"
        f"{middle_part}\n\n"
        f"[... continued ...]\n\n"
        f"{last_part}"
    )

    logger.info(f"Text truncated: {len(text):,} -> {len(truncated):,} chars")
    return truncated


def _parse_claude_response(response: str) -> dict:
    """Parse JSON from Claude response, handling various formats."""
    response = response.strip()

    # Try direct JSON parse
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Try to find JSON in markdown code block
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find any JSON object in response
    json_match = re.search(r'\{[^{}]*"date"[^{}]*"description"[^{}]*\}', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from response: {response[:200]}...")


def _get_model_flag(model: ModelType) -> str:
    """Get the Claude CLI model flag."""
    model_map = {
        "haiku": "haiku",
        "sonnet": "sonnet",
        "opus": "opus",
    }
    return model_map.get(model, "sonnet")


def suggest_name(text: str, model: Optional[ModelType] = None) -> NamingResult:
    """
    Use Claude Code CLI to suggest a filename based on document text.

    Args:
        text: Extracted text from the PDF
        model: Model to use (haiku/sonnet/opus). Defaults to settings.model

    Returns:
        NamingResult with suggested filename components
    """
    model = model or settings.model

    # Get model-specific context limit
    max_chars = MAX_CONTEXT_CHARS.get(model, 50000)

    # Reserve space for prompt template (~500 chars)
    max_text_chars = max_chars - 1000

    # Smart truncate if needed
    text = _smart_truncate(text, max_text_chars)

    prompt = NAMING_PROMPT.format(text=text)

    logger.info(f"Requesting naming suggestion from Claude ({model})...")
    logger.debug(f"Prompt length: {len(prompt)} chars")

    try:
        # Call Claude Code CLI (pass prompt via stdin to avoid CLI length limits)
        result = subprocess.run(
            ["claude", "--print", "--model", _get_model_flag(model)],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            encoding='utf-8',
        )

        if result.returncode != 0:
            logger.error(f"Claude CLI error: {result.stderr}")
            raise RuntimeError(f"Claude CLI failed: {result.stderr}")

        response = result.stdout.strip()
        logger.debug(f"Claude response: {response[:500]}...")

        # Parse the response
        parsed = _parse_claude_response(response)

        # Validate and clean the response
        date = parsed.get("date")
        if date and not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
            logger.warning(f"Invalid date format '{date}', ignoring")
            date = None

        description = parsed.get("description", "Unknown_Document")
        description = _clean_filename(description)

        confidence = float(parsed.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        reasoning = parsed.get("reasoning", "No reasoning provided")

        return NamingResult(
            date=date,
            description=description,
            confidence=confidence,
            reasoning=reasoning,
            model_used=model,
            raw_response=response,
        )

    except subprocess.TimeoutExpired:
        logger.error("Claude CLI timed out")
        raise RuntimeError("Claude CLI timed out after 120 seconds")
    except FileNotFoundError:
        logger.error("Claude CLI not found - ensure 'claude' is in PATH")
        raise RuntimeError("Claude CLI not found. Please install Claude Code and ensure it's in PATH")
    except Exception as e:
        logger.error(f"Error calling Claude: {e}")
        raise


def check_claude_available() -> bool:
    """Check if Claude Code CLI is available."""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False
