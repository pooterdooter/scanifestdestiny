# PDF Scan Organizer

A local-first PDF analysis and intelligent renaming tool. Extracts text from PDFs (native text or OCR for scanned documents), uses Claude AI to suggest descriptive filenames, and learns from patterns over time.

## Features

- **Hybrid Text Extraction** - Automatically detects text-based vs scanned PDFs and applies OCR when needed
- **AI-Powered Naming** - Uses Claude Code CLI to analyze document content and suggest meaningful filenames
- **Model Selection** - Toggle between Haiku (fast), Sonnet (balanced), and Opus (accurate)
- **Speed Modes** - Fast (1 page, 150 DPI), Balanced (3 pages, 200 DPI), Thorough (all pages, 300 DPI)
- **Learning System** - Remembers document patterns and applies consistent naming to similar documents
- **User Corrections** - Learns from manual renames to improve future suggestions
- **Rename Ledger** - Complete history of all operations with timestamps and confidence scores
- **Privacy First** - All processing is local; only extracted text is sent to Claude for naming

## Requirements

- Python 3.10+
- [Claude Code CLI](https://claude.ai/code) installed and authenticated
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) (for scanned PDFs)

## Installation

### 1. Clone or Download

```bash
git clone <repository-url>
cd scan-organizer
```

### 2. Run Setup

```powershell
.\setup_venv.bat
```

This will:
- Create a Python virtual environment
- Install dependencies (pymupdf, pytesseract, Pillow)
- Verify Tesseract and Claude CLI availability

### 3. Install Tesseract OCR (if not already installed)

Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

Add to PATH (typically `C:\Program Files\Tesseract-OCR`)

## Usage

### Process PDFs

```powershell
# Single file
.\run.bat process "C:\path\to\document.pdf"

# Entire folder
.\run.bat process "C:\path\to\scans"

# Recursive (include subfolders)
.\run.bat process "C:\path\to\scans" --recursive
```

### Options

| Flag | Description |
|------|-------------|
| `-m, --model` | Claude model: `haiku`, `sonnet` (default), `opus` |
| `-s, --speed` | Processing speed: `fast`, `balanced` (default), `thorough` |
| `-n, --dry-run` | Preview renames without making changes |
| `-f, --force` | Re-process files already in ledger |
| `-r, --recursive` | Process subdirectories |
| `-v, --verbose` | Enable debug output |

### Examples

```powershell
# Fast processing with Haiku (quick categorization)
.\run.bat process "C:\scans" --model haiku --speed fast

# Maximum accuracy with Opus (important documents)
.\run.bat process "C:\scans" --model opus --speed thorough

# Preview changes first
.\run.bat process "C:\scans" --dry-run

# Re-process a file with different settings
.\run.bat process "C:\scans\doc.pdf" --force --model opus
```

### View History

```powershell
# Last 10 renames
.\run.bat history

# Last 50 renames
.\run.bat history --last 50

# Summary statistics
.\run.bat history --summary
```

### Learning System

```powershell
# View learning statistics
.\run.bat learn --stats

# Scan for manual corrections (files you renamed after processing)
.\run.bat learn --scan-corrections
```

### PDF Info

```powershell
# View PDF metadata without processing
.\run.bat info "C:\path\to\document.pdf"
```

## Output Format

Files are renamed to: `YYYY-MM-DD_Description.pdf`

Examples:
- `2024-11-08_Kingdom_Heights_HOA_2025_Assessment.pdf`
- `2025-03-10_LoanDepot_Mortgage_Statement.pdf`
- `2025-11-01_RapidCare_ER_Visit_Kaito_Glaser.pdf`

If no date is found: `YYYY-MM-DD_UNDATED_Description.pdf` (uses processing date)

## Project Structure

```
scan-organizer/
├── src/
│   ├── main.py           # CLI entry point
│   ├── pdf_extractor.py  # Text/OCR extraction
│   ├── claude_namer.py   # Claude Code CLI integration
│   ├── learning.py       # Pattern memory + corrections
│   ├── ledger.py         # Rename history tracking
│   └── config.py         # Settings
├── data/                 # Local data (gitignored)
│   ├── ledger.json       # Rename history
│   ├── patterns.json     # Learned patterns
│   └── corrections.json  # User corrections
├── logs/                 # Operation logs (gitignored)
├── setup_venv.bat        # One-time setup
├── run.bat               # Run the tool
└── requirements.txt
```

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
3. If ≥50% keyword overlap, applies the pattern (skips Claude API)
4. Tracks `times_applied` and `confidence_avg`

### User Corrections
If you manually rename a processed file:
1. Run `.\run.bat learn --scan-corrections`
2. Confirm the correction
3. Future similar documents will use your preferred name

## Privacy & Security

- **Local Processing** - PDF text extraction happens entirely on your machine
- **Claude Integration** - Only extracted text (not the PDF itself) is sent to Claude for naming
- **No Telemetry** - No usage data is collected or transmitted
- **Gitignored Data** - Ledger, patterns, and logs contain potentially private info and are excluded from git

## Dependencies

| Package | Version | Purpose | License |
|---------|---------|---------|---------|
| [PyMuPDF](https://pymupdf.readthedocs.io/) | ≥1.24.0 | PDF text extraction & rendering | AGPL-3.0 |
| [pytesseract](https://github.com/madmaze/pytesseract) | ≥0.3.10 | Tesseract OCR wrapper | Apache-2.0 |
| [Pillow](https://python-pillow.org/) | ≥10.0.0 | Image processing | HPND |

## Third-Party Licenses

This project uses Tesseract OCR and Leptonica. Their license notices are included below as required.

---

### Tesseract OCR

Tesseract is licensed under the Apache License, Version 2.0.

```
Copyright (C) 2006 Google Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

**NOTICE**: This project uses Tesseract OCR but does not modify its source code. Tesseract is invoked as an external dependency through the pytesseract Python wrapper.

For the full Apache 2.0 license text, see: https://www.apache.org/licenses/LICENSE-2.0

For Tesseract source code and documentation, see: https://github.com/tesseract-ocr/tesseract

---

### Leptonica

Tesseract depends on Leptonica, which is licensed under the BSD 2-Clause License.

```
Copyright (C) 2001-2024 Leptonica
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
```

For Leptonica source code and documentation, see: http://leptonica.org/

---

## Troubleshooting

### "Tesseract not found"
- Install Tesseract from https://github.com/UB-Mannheim/tesseract/wiki
- Add installation directory to PATH (e.g., `C:\Program Files\Tesseract-OCR`)
- Restart your terminal

### "Claude CLI not found"
- Install Claude Code: https://claude.ai/code
- Ensure `claude` command is accessible from terminal
- Run `claude --version` to verify

### "No text could be extracted"
- The PDF may be a scanned image requiring OCR
- Ensure Tesseract is installed
- Try `--speed thorough` for better OCR results

### Pattern matching too aggressive
- Edit `src/learning.py` and adjust the `0.5` threshold in `find_matching_pattern()`
- Or use `--force` to bypass pattern matching for specific files

## License

This project is provided as-is for personal use. See Third-Party Licenses section for dependencies.

## Acknowledgments

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - Open source OCR engine
- [Leptonica](http://leptonica.org/) - Image processing library
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF processing library
- [Claude](https://claude.ai/) - AI assistance for document analysis
