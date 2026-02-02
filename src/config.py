"""Configuration settings for PDF Scan Organizer."""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# File paths
LEDGER_FILE = DATA_DIR / "ledger.json"
PATTERNS_FILE = DATA_DIR / "patterns.json"
CORRECTIONS_FILE = DATA_DIR / "corrections.json"
LOG_FILE = LOGS_DIR / "scan-organizer.log"

# Type definitions
ModelType = Literal["haiku", "sonnet", "opus"]
SpeedMode = Literal["fast", "balanced", "thorough"]


@dataclass
class Settings:
    """Runtime configuration settings."""

    model: ModelType = "sonnet"
    speed_mode: SpeedMode = "balanced"
    ocr_language: str = "eng"
    date_format: str = "%Y-%m-%d"
    dry_run: bool = False
    verbose: bool = False

    # OCR settings per speed mode
    ocr_dpi: dict = field(default_factory=lambda: {
        "fast": 150,
        "balanced": 200,
        "thorough": 300,
    })

    # Pages to process per speed mode
    max_pages: dict = field(default_factory=lambda: {
        "fast": 1,
        "balanced": 3,
        "thorough": 0,  # 0 = all pages
    })

    # Minimum text length to consider a page as text-based (not scanned)
    min_text_threshold: int = 50

    def get_ocr_dpi(self) -> int:
        """Get OCR DPI for current speed mode."""
        return self.ocr_dpi[self.speed_mode]

    def get_max_pages(self) -> int:
        """Get max pages to process for current speed mode."""
        return self.max_pages[self.speed_mode]


# Global settings instance (can be modified at runtime)
settings = Settings()
