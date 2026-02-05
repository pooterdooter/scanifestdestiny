# Scanifest Destiny

A local-first PDF analysis and intelligent renaming tool. Extracts text from PDFs (native text or OCR for scanned documents), uses Claude AI to suggest descriptive filenames, and learns from patterns over time.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

## Features

- **Intelligent Renaming** - AI-powered filename suggestions based on document content
- **Hybrid Text Extraction** - Automatically detects text-based vs scanned PDFs and applies OCR when needed
- **Multi-Document Detection** - Detects and splits PDFs containing multiple documents scanned together
- **CSV Metadata Extraction** - Extract specific fields from documents using customizable templates
- **Learning System** - Remembers document patterns for consistent naming
- **Model Selection** - Toggle between Haiku (fast), Sonnet (balanced), and Opus (accurate)
- **Privacy First** - All processing is local; only extracted text is sent to Claude for analysis
- **Cross-Platform** - Works on Windows, macOS, and Linux

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Linux](#linux)
- [Quick Start](#quick-start)
- [Commands](#commands)
  - [process](#process---rename-pdfs)
  - [split](#split---split-multi-document-pdfs)
  - [extract](#extract---csv-metadata-extraction)
  - [history](#history---view-rename-history)
  - [learn](#learn---manage-learning-system)
  - [info](#info---view-pdf-metadata)
- [Usage Examples](#usage-examples)
- [CSV Template Extraction](#csv-template-extraction)
- [How Learning Works](#how-learning-works)
- [Confidence Scoring](#confidence-scoring)
- [Smart Text Handling](#smart-text-handling)
- [Troubleshooting](#troubleshooting)
- [Privacy & Security](#privacy--security)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Requirements

- **Python 3.10+** - [Download Python](https://www.python.org/downloads/)
- **Claude Code CLI** - [Install Claude Code](https://claude.ai/code)
- **Tesseract OCR** (optional, for scanned PDFs) - See installation instructions below

## Installation

### Windows

1. **Install Python 3.10+** from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"

2. **Install Claude Code CLI**
   ```powershell
   # Follow instructions at https://claude.ai/code
   # Verify installation:
   claude --version
   ```

3. **Install Tesseract OCR** (optional, for scanned PDFs)
   - Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
   - During installation, note the install path (default: `C:\Program Files\Tesseract-OCR`)
   - Add to PATH: System Properties > Environment Variables > Path > Add the install directory

4. **Clone and setup the project**
   ```powershell
   git clone https://github.com/YOUR_USERNAME/scanifestdestiny.git
   cd scanifestdestiny
   .\setup_venv.bat
   ```

5. **Verify installation**
   ```powershell
   .\run.bat --help
   ```

### macOS

1. **Install Python 3.10+** (if not already installed)
   ```bash
   # Using Homebrew
   brew install python@3.11
   ```

2. **Install Claude Code CLI**
   ```bash
   # Follow instructions at https://claude.ai/code
   # Verify installation:
   claude --version
   ```

3. **Install Tesseract OCR** (optional, for scanned PDFs)
   ```bash
   brew install tesseract
   ```

4. **Clone and setup the project**
   ```bash
   git clone https://github.com/YOUR_USERNAME/scanifestdestiny.git
   cd scanifestdestiny
   chmod +x setup.sh run.sh
   ./setup.sh
   ```

5. **Verify installation**
   ```bash
   ./run.sh --help
   ```

### Linux

#### Ubuntu/Debian

1. **Install Python 3.10+**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv
   ```

2. **Install Claude Code CLI**
   ```bash
   # Follow instructions at https://claude.ai/code
   # Verify installation:
   claude --version
   ```

3. **Install Tesseract OCR** (optional, for scanned PDFs)
   ```bash
   sudo apt install tesseract-ocr
   ```

4. **Clone and setup the project**
   ```bash
   git clone https://github.com/YOUR_USERNAME/scanifestdestiny.git
   cd scanifestdestiny
   chmod +x setup.sh run.sh
   ./setup.sh
   ```

#### Fedora

```bash
sudo dnf install python3 python3-pip tesseract
```

#### Arch Linux

```bash
sudo pacman -S python python-pip tesseract
```

## Quick Start

```bash
# Windows
.\run.bat process "C:\path\to\scans"

# macOS/Linux
./run.sh process "/path/to/scans"
```

This will:
1. Find all PDFs in the specified directory
2. Extract text (using OCR if needed)
3. Analyze content with Claude AI
4. Rename files to `YYYY-MM-DD_Description.pdf` format

## Commands

### process - Rename PDFs

Extract text, analyze content, and rename files intelligently.

```bash
# Windows
.\run.bat process <path> [options]

# macOS/Linux
./run.sh process <path> [options]
```

| Option | Description |
|--------|-------------|
| `-m, --model` | Claude model: `haiku`, `sonnet` (default), `opus` |
| `-s, --speed` | OCR quality: `fast`, `balanced` (default), `thorough` |
| `-n, --dry-run` | Preview renames without making changes |
| `-f, --force` | Re-process files already in ledger |
| `-r, --recursive` | Process subdirectories |
| `--no-patterns` | Skip learned patterns, always use Claude |
| `--split` | Detect and offer to split multi-document PDFs |

### split - Split Multi-Document PDFs

Detect and split PDFs containing multiple documents (no renaming).

```bash
# Windows
.\run.bat split <path> [options]

# macOS/Linux
./run.sh split <path> [options]
```

| Option | Description |
|--------|-------------|
| `-m, --model` | Claude model for boundary detection |
| `-a, --analyze-only` | Show detected splits without modifying files |
| `-r, --recursive` | Process subdirectories |

### extract - CSV Metadata Extraction

Extract specific fields from PDFs using a CSV template.

```bash
# Windows
.\run.bat extract <path> --template template.csv [options]

# macOS/Linux
./run.sh extract <path> --template template.csv [options]
```

| Option | Description |
|--------|-------------|
| `-t, --template` | CSV template file with column headers as fields |
| `-o, --output` | Output CSV file path |
| `-m, --model` | Claude model: `haiku`, `sonnet` (default), `opus` |
| `-r, --recursive` | Process subdirectories |
| `--create-template` | Create a blank template with specified fields |
| `--no-metadata` | Exclude file info columns from output |

### history - View Rename History

```bash
# Windows
.\run.bat history [options]

# macOS/Linux
./run.sh history [options]
```

| Option | Description |
|--------|-------------|
| `-l, --last N` | Show last N entries (default: 10) |
| `--summary` | Show statistics |

### learn - Manage Learning System

```bash
# Windows
.\run.bat learn [options]

# macOS/Linux
./run.sh learn [options]
```

| Option | Description |
|--------|-------------|
| `--stats` | Show pattern statistics |
| `--scan-corrections` | Learn from manual renames |

### info - View PDF Metadata

```bash
# Windows
.\run.bat info <path>

# macOS/Linux
./run.sh info <path>
```

## Usage Examples

### Basic Renaming

```bash
# Process a single file
./run.sh process "document.pdf"

# Process a folder
./run.sh process "/path/to/scans"

# Process with subfolders
./run.sh process "/path/to/scans" --recursive
```

### Speed vs Accuracy

```bash
# Fast: Haiku model, quick OCR
./run.sh process "/scans" --model haiku --speed fast

# Balanced: Sonnet model (default)
./run.sh process "/scans"

# Thorough: Opus model, high-quality OCR
./run.sh process "/scans" --model opus --speed thorough
```

### Development & Testing

```bash
# Preview without changes
./run.sh process "/scans" --dry-run

# Force re-process all files
./run.sh process "/scans" --force

# Always use Claude (bypass patterns)
./run.sh process "/scans" --no-patterns

# Full re-analysis
./run.sh process "/scans" --force --no-patterns --model opus
```

### Multi-Document PDFs

```bash
# Preview splits
./run.sh split "/scans" --analyze-only

# Interactive split
./run.sh split "/scans"

# Split + rename in one command
./run.sh process "/scans" --split
```

## CSV Template Extraction

Extract specific fields from documents into a CSV file.

### Pre-built Templates

The `templates/` folder includes ready-to-use templates:

```bash
# Use the universal template (invoices, bills, medical, etc.)
./run.sh extract "/path/to/pdfs" --template templates/extraction_template.csv -o results.csv
```

See `templates/README.md` for field descriptions and usage tips.

### Create a Custom Template

```bash
# Create a template with specific fields
./run.sh extract --create-template "Invoice Number,Date,Amount,Vendor Name" -o template.csv
```

This creates `template.csv`:
```csv
Invoice Number,Date,Amount,Vendor Name
```

### Extract Metadata

```bash
# Extract fields from PDFs
./run.sh extract "/path/to/invoices" --template template.csv --output results.csv
```

Output `results.csv`:
```csv
_file_name,_file_path,Invoice Number,Date,Amount,Vendor Name,_confidence,_extraction_method,_errors
invoice1.pdf,/path/invoice1.pdf,INV-2024-001,2024-01-15,1500.00,Acme Corp,100%,text,
invoice2.pdf,/path/invoice2.pdf,INV-2024-002,2024-01-20,2300.50,Tech Inc,75%,ocr,
```

### Example Use Cases

- **Invoice Processing**: Extract invoice numbers, dates, amounts, vendor names
- **Medical Records**: Extract patient names, dates, procedure codes
- **Legal Documents**: Extract case numbers, dates, party names
- **Receipts**: Extract merchant, date, total, payment method

## How Learning Works

### Pattern Creation

When Claude successfully names a file (≥75% confidence):
1. Extracts distinctive keywords from the document
2. Stores the filename as a template
3. Links keywords to the template

### Pattern Matching

When processing a new file:
1. Extracts keywords from the document
2. Compares against stored patterns
3. If ≥50% keyword overlap, applies the pattern (skips Claude)
4. Tracks usage statistics

### User Corrections

If you manually rename a processed file:
1. Run `./run.sh learn --scan-corrections`
2. Confirm the corrections
3. Future similar documents use your preferred names

## Confidence Scoring

The tool calculates confidence differently depending on the operation:

### File Naming (process command)

| Source | How Confidence is Calculated |
|--------|------------------------------|
| **Claude AI** | Self-reported by the AI based on document clarity, date certainty, and description accuracy (0-100%) |
| **Pattern Match** | `keyword_overlap_score × pattern_average_confidence` |
| **User Correction** | Always 100% (user-provided names are trusted) |

### Metadata Extraction (extract command)

```
confidence = (fields_found / total_fields_requested) × 100%
```

For example, if you request 10 fields and the AI finds values for 7:
- Confidence = 7/10 = **70%**

### Document Splitting (split command)

Claude AI reports confidence for each detected document boundary based on:
- Clear visual/content separation between documents
- Distinct document types identified
- Page number continuity

### Pattern Learning Threshold

- **≥75% confidence**: Pattern is created and stored for future use
- **<75% confidence**: Document is processed but no pattern is saved

## Smart Text Handling

### Context Window Management

Large documents are automatically truncated to fit model context limits:

| Model | Max Context | Use Case |
|-------|-------------|----------|
| Haiku | ~50,000 chars | Fast processing, simple documents |
| Sonnet | ~100,000 chars | Balanced (default) |
| Opus | ~150,000 chars | Complex documents, highest accuracy |

### Smart Truncation Strategy

When a document exceeds the context limit:

```
[First 60%] - Headers, document type, dates (most important info)
[... truncated ...]
[Middle 20%] - Sampled content for context
[... continued ...]
[Last 20%]  - Signatures, totals, conclusions
```

This preserves the most useful information for analysis while staying within limits.

### Cross-Platform Compatibility

Text is passed to Claude via stdin (not command-line arguments) to avoid platform-specific length limits:
- Windows CMD: ~8,191 char limit (bypassed)
- macOS/Linux: ~256KB-2MB limits (bypassed)

This ensures reliable processing of large documents on all platforms.

## Troubleshooting

### "Tesseract not found"

**Windows:**
- Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
- Add install directory to PATH
- Restart terminal

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr

# Fedora
sudo dnf install tesseract

# Arch
sudo pacman -S tesseract
```

### "Claude CLI not found"

- Install Claude Code from [claude.ai/code](https://claude.ai/code)
- Ensure `claude` command is in PATH
- Run `claude --version` to verify

### "No text could be extracted"

- The PDF may be a scanned image requiring OCR
- Ensure Tesseract is installed
- Try `--speed thorough` for better OCR results

### Large PDFs / Context Overflow

The tool automatically handles large documents. See [Smart Text Handling](#smart-text-handling) for details.

If you still encounter issues:
- Use `--model opus` for larger context window (150k chars)
- Ensure the PDF isn't corrupted
- Check `logs/scanifestdestiny.log` for detailed error messages

### Pattern Matching Too Aggressive

- Use `--no-patterns` to bypass patterns for specific runs
- Or edit `data/patterns.json` to remove unwanted patterns

## Privacy & Security

- **Local Processing** - PDF text extraction happens entirely on your machine
- **Claude Integration** - Only extracted text (not the PDF itself) is sent to Claude
- **No Telemetry** - No usage data is collected or transmitted
- **Gitignored Data** - Ledger, patterns, and logs are excluded from git
- **No Network (except Claude)** - No other internet connections are made

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Start for Contributors

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/scanifestdestiny.git
cd scanifestdestiny

# Setup development environment
./setup.sh  # or .\setup_venv.bat on Windows

# Make changes, then submit a pull request
```

## License

This project is licensed under the Apache License 2.0 - see [LICENSE](LICENSE) for details.

### Third-Party Licenses

This project uses the following open-source libraries:

| Library | License | Link |
|---------|---------|------|
| PyMuPDF | AGPL-3.0 | [pymupdf.io](https://pymupdf.io) |
| pytesseract | Apache-2.0 | [github.com/madmaze/pytesseract](https://github.com/madmaze/pytesseract) |
| Pillow | HPND | [python-pillow.org](https://python-pillow.org) |
| Tesseract OCR | Apache-2.0 | [github.com/tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract) |
| Leptonica | BSD-2-Clause | [leptonica.org](http://leptonica.org) |

See [THIRD_PARTY_LICENSES](THIRD_PARTY_LICENSES) for full license texts.

## Acknowledgments

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - Open source OCR engine
- [Leptonica](http://leptonica.org/) - Image processing library
- [PyMuPDF](https://pymupdf.io/) - PDF processing library
- [Claude](https://claude.ai/) - AI assistance for document analysis

---

**Made with Claude Code**
