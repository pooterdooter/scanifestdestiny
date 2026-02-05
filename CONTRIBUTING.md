# Contributing to Scanifest Destiny

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Requesting Features](#requesting-features)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Please:

- Be respectful and constructive in discussions
- Welcome newcomers and help them get started
- Focus on the technical merits of contributions
- Accept constructive criticism gracefully

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/scanifestdestiny.git
   cd scanifestdestiny
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/scanifestdestiny.git
   ```
4. **Set up your development environment** (see [Development Setup](#development-setup))

## How to Contribute

### Types of Contributions

- **Bug fixes**: Fix issues and improve stability
- **New features**: Add new functionality (please discuss first)
- **Documentation**: Improve docs, fix typos, add examples
- **Tests**: Add or improve test coverage
- **Performance**: Optimize code for speed or memory usage

### Before You Start

1. **Check existing issues** to avoid duplicate work
2. **Open an issue** to discuss significant changes before implementing
3. **Keep changes focused** - one feature/fix per pull request

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- Claude Code CLI (for testing AI features)
- Tesseract OCR (for testing OCR features)

### Setup Steps

**Windows:**
```powershell
git clone https://github.com/YOUR_USERNAME/scanifestdestiny.git
cd scanifestdestiny
.\setup_venv.bat
```

**macOS/Linux:**
```bash
git clone https://github.com/YOUR_USERNAME/scanifestdestiny.git
cd scanifestdestiny
chmod +x setup.sh run.sh
./setup.sh
```

### Running the Tool

**Windows:**
```powershell
.\run.bat --help
```

**macOS/Linux:**
```bash
./run.sh --help
```

### Project Structure

```
scanifestdestiny/
├── src/
│   ├── main.py              # CLI entry point
│   ├── pdf_extractor.py     # PDF text/OCR extraction
│   ├── pdf_splitter.py      # Multi-doc detection & splitting
│   ├── claude_namer.py      # Claude CLI integration
│   ├── metadata_extractor.py # CSV template extraction
│   ├── learning.py          # Pattern learning system
│   ├── ledger.py            # Rename history
│   └── config.py            # Configuration
├── data/                    # Runtime data (gitignored)
├── logs/                    # Log files (gitignored)
├── setup.sh                 # Unix setup script
├── setup_venv.bat           # Windows setup script
├── run.sh                   # Unix run script
├── run.bat                  # Windows run script
└── requirements.txt         # Python dependencies
```

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use meaningful variable and function names
- Add docstrings to all public functions and classes
- Keep functions focused and under 50 lines when possible

### Code Quality

- No hardcoded paths or credentials
- Handle errors gracefully with informative messages
- Use type hints for function signatures
- Log important operations (use the `logging` module)

### Example

```python
def process_document(pdf_path: Path, model: str = "sonnet") -> Optional[str]:
    """
    Process a PDF document and return the suggested filename.

    Args:
        pdf_path: Path to the PDF file
        model: Claude model to use for analysis

    Returns:
        Suggested filename or None if processing failed
    """
    logger = logging.getLogger(__name__)

    if not pdf_path.exists():
        logger.error(f"File not found: {pdf_path}")
        return None

    # ... implementation
```

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(extract): add CSV template metadata extraction

fix(ocr): handle empty pages gracefully

docs: update installation instructions for Linux
```

## Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the coding standards

3. **Test your changes**:
   - Test on your platform (Windows/macOS/Linux)
   - Test with both text-based and scanned PDFs if applicable
   - Ensure existing functionality still works

4. **Commit your changes** with descriptive commit messages

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**:
   - Use a clear, descriptive title
   - Reference any related issues
   - Describe what changes you made and why
   - Include testing notes

7. **Respond to feedback** and make requested changes

### PR Checklist

- [ ] Code follows the project's style guidelines
- [ ] Self-review completed
- [ ] Changes are documented (README, docstrings, etc.)
- [ ] No new warnings or errors introduced
- [ ] Cross-platform compatibility considered

## Reporting Bugs

When reporting bugs, please include:

1. **Description**: Clear description of the bug
2. **Steps to reproduce**: Minimal steps to reproduce the issue
3. **Expected behavior**: What you expected to happen
4. **Actual behavior**: What actually happened
5. **Environment**:
   - Operating system and version
   - Python version
   - Tool version (`.\run.bat --version`)
6. **Logs**: Relevant log output (check `logs/scanifestdestiny.log`)
7. **Sample files**: If possible, provide a sample PDF (without private data)

### Bug Report Template

```markdown
**Description**
A clear description of the bug.

**Steps to Reproduce**
1. Run command `...`
2. Select option `...`
3. See error

**Expected Behavior**
What should happen.

**Actual Behavior**
What actually happens.

**Environment**
- OS: Windows 11 / macOS 14 / Ubuntu 22.04
- Python: 3.11.5
- Tool version: 1.0.0

**Logs**
```
Paste relevant log output here
```
```

## Requesting Features

For feature requests:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case**: Why do you need this feature?
3. **Propose a solution**: How do you envision it working?
4. **Consider alternatives**: Are there other ways to solve this?

### Feature Request Template

```markdown
**Use Case**
Describe the problem you're trying to solve.

**Proposed Solution**
Describe how you'd like it to work.

**Alternatives Considered**
Other approaches you've considered.

**Additional Context**
Any other relevant information.
```

## Questions?

If you have questions about contributing, feel free to:

1. Open a [Discussion](https://github.com/OWNER/scanifestdestiny/discussions) on GitHub
2. Ask in an existing related issue
3. Reach out to the maintainers

Thank you for contributing!
