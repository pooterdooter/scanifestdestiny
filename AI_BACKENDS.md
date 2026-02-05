# AI Backend Configuration Guide

This guide explains how to switch Scanifest Destiny between different AI backends for document analysis and naming suggestions.

## Table of Contents

1. [Current Implementation (Claude Code CLI)](#current-implementation-claude-code-cli)
2. [Switching to Claude API](#switching-to-claude-api)
3. [Switching to OpenAI (ChatGPT)](#switching-to-openai-chatgpt)
4. [Switching to Google Gemini](#switching-to-google-gemini)
5. [Switching to Local Models](#switching-to-local-models)
6. [Architecture Overview](#architecture-overview)

---

## Current Implementation (Claude Code CLI)

The tool currently uses the Claude Code CLI via subprocess:

```python
# src/claude_namer.py
result = subprocess.run(
    ["claude", "--print", "--model", model, prompt],
    capture_output=True,
    text=True,
    timeout=120,
)
```

**Requirements:**
- Claude Code CLI installed and authenticated
- Valid Claude subscription (Pro, Max, or Team)

**Available models:**
- `haiku` - Fast, cost-effective
- `sonnet` - Balanced (default)
- `opus` - Most capable

---

## Switching to Claude API

### Step 1: Install the Anthropic SDK

```bash
pip install anthropic
```

Add to `requirements.txt`:
```
anthropic>=0.40.0
```

### Step 2: Set Your API Key

```bash
# Windows
set ANTHROPIC_API_KEY=sk-ant-...

# macOS/Linux
export ANTHROPIC_API_KEY=sk-ant-...
```

Or create a `.env` file (already gitignored):
```
ANTHROPIC_API_KEY=sk-ant-...
```

### Step 3: Modify `src/claude_namer.py`

Replace the subprocess implementation:

```python
"""Claude API integration for intelligent file naming."""

import json
import logging
import re
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from anthropic import Anthropic

from .config import settings, ModelType

logger = logging.getLogger(__name__)

# Initialize client (uses ANTHROPIC_API_KEY env var)
client = Anthropic()

# Model mapping to full API names
MODEL_MAP = {
    "haiku": "claude-haiku-4-20250514",
    "sonnet": "claude-sonnet-4-20250514",
    "opus": "claude-opus-4-20250514",
}

# Context limits (in characters, conservative)
MAX_CONTEXT_CHARS = {
    "haiku": 50000,
    "sonnet": 100000,
    "opus": 150000,
}

# ... keep NAMING_PROMPT, NamingResult, _clean_filename, _smart_truncate, _parse_claude_response ...

def suggest_name(text: str, model: Optional[ModelType] = None) -> NamingResult:
    """Use Claude API to suggest a filename based on document text."""
    model = model or settings.model
    model_id = MODEL_MAP.get(model, MODEL_MAP["sonnet"])

    # Smart truncate if needed
    max_chars = MAX_CONTEXT_CHARS.get(model, 50000)
    text = _smart_truncate(text, max_chars - 1000)

    prompt = NAMING_PROMPT.format(text=text)

    logger.info(f"Requesting naming suggestion from Claude API ({model})...")

    try:
        response = client.messages.create(
            model=model_id,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text.strip()
        parsed = _parse_claude_response(response_text)

        # ... rest of parsing logic stays the same ...

    except Exception as e:
        logger.error(f"Claude API error: {e}")
        raise


def check_claude_available() -> bool:
    """Check if Claude API is configured."""
    try:
        # Quick test call
        client.messages.create(
            model="claude-haiku-4-20250514",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        return True
    except Exception:
        return False
```

### Cost Comparison (API vs CLI)

| Method | Pricing |
|--------|---------|
| Claude Code CLI | Included with Pro/Max subscription |
| Claude API | Pay-per-token (~$3/M input, ~$15/M output for Sonnet) |

---

## Switching to OpenAI (ChatGPT)

### Step 1: Install the OpenAI SDK

```bash
pip install openai
```

Add to `requirements.txt`:
```
openai>=1.0.0
```

### Step 2: Set Your API Key

```bash
# Windows
set OPENAI_API_KEY=sk-...

# macOS/Linux
export OPENAI_API_KEY=sk-...
```

### Step 3: Create `src/openai_namer.py`

```python
"""OpenAI integration for intelligent file naming."""

import json
import logging
import re
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from openai import OpenAI

from .config import settings

logger = logging.getLogger(__name__)

client = OpenAI()  # Uses OPENAI_API_KEY env var

# Model mapping
MODEL_MAP = {
    "fast": "gpt-4o-mini",       # Fast, cheap
    "balanced": "gpt-4o",         # Balanced
    "powerful": "gpt-4-turbo",    # Most capable
}

# Context limits (characters)
MAX_CONTEXT_CHARS = {
    "fast": 40000,
    "balanced": 80000,
    "powerful": 100000,
}

NAMING_PROMPT = '''...'''  # Same prompt as before

# ... keep NamingResult, _clean_filename, _smart_truncate, _parse_response ...

def suggest_name(text: str, model: str = "balanced") -> NamingResult:
    """Use OpenAI to suggest a filename based on document text."""
    model_id = MODEL_MAP.get(model, MODEL_MAP["balanced"])

    max_chars = MAX_CONTEXT_CHARS.get(model, 40000)
    text = _smart_truncate(text, max_chars - 1000)

    prompt = NAMING_PROMPT.format(text=text)

    logger.info(f"Requesting naming suggestion from OpenAI ({model})...")

    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.3,  # Lower for more consistent output
        )

        response_text = response.choices[0].message.content.strip()
        parsed = _parse_response(response_text)

        # ... parsing logic ...

    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise
```

### Step 4: Update Imports in `src/main.py`

```python
# Change this:
from .claude_namer import suggest_name, check_claude_available

# To this:
from .openai_namer import suggest_name, check_openai_available as check_claude_available
```

---

## Switching to Google Gemini

### Step 1: Install the Google SDK

```bash
pip install google-generativeai
```

Add to `requirements.txt`:
```
google-generativeai>=0.5.0
```

### Step 2: Set Your API Key

```bash
# Windows
set GOOGLE_API_KEY=...

# macOS/Linux
export GOOGLE_API_KEY=...
```

### Step 3: Create `src/gemini_namer.py`

```python
"""Google Gemini integration for intelligent file naming."""

import json
import logging
import re
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

import google.generativeai as genai

from .config import settings

logger = logging.getLogger(__name__)

# Configure with API key from environment
genai.configure()

# Model mapping
MODEL_MAP = {
    "fast": "gemini-1.5-flash",
    "balanced": "gemini-1.5-pro",
    "powerful": "gemini-1.5-pro",
}

NAMING_PROMPT = '''...'''  # Same prompt

def suggest_name(text: str, model: str = "balanced") -> NamingResult:
    """Use Gemini to suggest a filename based on document text."""
    model_id = MODEL_MAP.get(model, MODEL_MAP["balanced"])
    model_instance = genai.GenerativeModel(model_id)

    text = _smart_truncate(text, 80000)
    prompt = NAMING_PROMPT.format(text=text)

    logger.info(f"Requesting naming suggestion from Gemini ({model})...")

    try:
        response = model_instance.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=1024,
                temperature=0.3,
            )
        )

        response_text = response.text.strip()
        parsed = _parse_response(response_text)

        # ... parsing logic ...

    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise
```

---

## Switching to Local Models

For privacy-focused deployments, you can run models locally using Ollama.

### Step 1: Install Ollama

Download from [ollama.ai](https://ollama.ai) and install.

### Step 2: Pull a Model

```bash
ollama pull llama3.1
ollama pull mistral
ollama pull phi3
```

### Step 3: Create `src/ollama_namer.py`

```python
"""Ollama (local model) integration for intelligent file naming."""

import json
import logging
import re
import requests
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from .config import settings

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"

MODEL_MAP = {
    "fast": "phi3",
    "balanced": "mistral",
    "powerful": "llama3.1",
}

NAMING_PROMPT = '''...'''  # Same prompt

def suggest_name(text: str, model: str = "balanced") -> NamingResult:
    """Use local Ollama model to suggest a filename."""
    model_id = MODEL_MAP.get(model, MODEL_MAP["balanced"])

    # Local models have smaller context, truncate more aggressively
    text = _smart_truncate(text, 20000)
    prompt = NAMING_PROMPT.format(text=text)

    logger.info(f"Requesting naming suggestion from Ollama ({model_id})...")

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model_id,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 1024,
                }
            },
            timeout=300,  # Local models can be slower
        )
        response.raise_for_status()

        response_text = response.json()["response"].strip()
        parsed = _parse_response(response_text)

        # ... parsing logic ...

    except Exception as e:
        logger.error(f"Ollama error: {e}")
        raise


def check_ollama_available() -> bool:
    """Check if Ollama is running."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False
```

**Pros of local models:**
- Complete privacy - no data leaves your machine
- No API costs
- Works offline

**Cons:**
- Requires decent hardware (8GB+ RAM)
- Generally less capable than cloud models
- Slower inference

---

## Architecture Overview

The AI integration is isolated to a single file, making it easy to swap backends:

```
src/
├── main.py              # CLI - imports from *_namer.py
├── claude_namer.py      # Current: Claude Code CLI
├── pdf_extractor.py     # PDF text extraction (unchanged)
├── pdf_splitter.py      # Uses same namer interface
├── metadata_extractor.py # Uses same namer interface
├── learning.py          # Pattern matching (unchanged)
├── ledger.py            # History tracking (unchanged)
└── config.py            # Configuration
```

### Creating a Custom Backend

All namer implementations should follow this interface:

```python
@dataclass
class NamingResult:
    date: Optional[str]       # YYYY-MM-DD or None
    description: str          # Filename description
    confidence: float         # 0.0 to 1.0
    reasoning: str            # Explanation
    model_used: str           # Model identifier
    raw_response: str         # Raw API response

def suggest_name(text: str, model: Optional[str] = None) -> NamingResult:
    """Suggest a filename based on document text."""
    ...

def check_available() -> bool:
    """Check if the backend is available."""
    ...
```

### Configuration Options

To make the backend configurable at runtime, modify `src/config.py`:

```python
from typing import Literal

AIBackend = Literal["claude-cli", "claude-api", "openai", "gemini", "ollama"]

@dataclass
class Settings:
    ai_backend: AIBackend = "claude-cli"
    model: str = "sonnet"
    # ... other settings
```

Then in `src/main.py`, dynamically import the appropriate backend:

```python
def get_namer():
    if settings.ai_backend == "claude-cli":
        from .claude_namer import suggest_name
    elif settings.ai_backend == "claude-api":
        from .claude_api_namer import suggest_name
    elif settings.ai_backend == "openai":
        from .openai_namer import suggest_name
    # ... etc
    return suggest_name
```

---

## Quick Reference

| Backend | Install | Auth | Cost |
|---------|---------|------|------|
| Claude Code CLI | `npm install -g @anthropic-ai/claude-code` | Login via CLI | Subscription |
| Claude API | `pip install anthropic` | `ANTHROPIC_API_KEY` | Pay-per-token |
| OpenAI | `pip install openai` | `OPENAI_API_KEY` | Pay-per-token |
| Gemini | `pip install google-generativeai` | `GOOGLE_API_KEY` | Free tier / Pay |
| Ollama | [ollama.ai](https://ollama.ai) | None (local) | Free |

---

## Questions?

If you implement a new backend, consider contributing it back to the project!
