"""Ledger system for tracking all rename operations."""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, asdict

from .config import LEDGER_FILE

logger = logging.getLogger(__name__)


@dataclass
class LedgerEntry:
    """A single rename operation record."""

    timestamp: str
    original_path: str
    original_name: str
    new_name: str
    new_path: str
    model_used: str
    confidence: float
    content_hash: str
    extraction_method: str
    pattern_id: Optional[str] = None
    reasoning: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "LedgerEntry":
        return cls(**data)


class Ledger:
    """Manages the rename history ledger."""

    def __init__(self, ledger_path: Path = LEDGER_FILE):
        self.ledger_path = ledger_path
        self._entries: List[LedgerEntry] = []
        self._load()

    def _load(self) -> None:
        """Load ledger from disk."""
        if self.ledger_path.exists():
            try:
                with open(self.ledger_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._entries = [LedgerEntry.from_dict(e) for e in data.get("entries", [])]
                logger.debug(f"Loaded {len(self._entries)} ledger entries")
            except Exception as e:
                logger.error(f"Failed to load ledger: {e}")
                self._entries = []
        else:
            self._entries = []

    def _save(self) -> None:
        """Save ledger to disk."""
        try:
            data = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "entries": [e.to_dict() for e in self._entries],
            }
            with open(self.ledger_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved {len(self._entries)} ledger entries")
        except Exception as e:
            logger.error(f"Failed to save ledger: {e}")
            raise

    def add_entry(
        self,
        original_path: Path,
        new_path: Path,
        model_used: str,
        confidence: float,
        content_hash: str,
        extraction_method: str,
        pattern_id: Optional[str] = None,
        reasoning: Optional[str] = None,
    ) -> LedgerEntry:
        """Add a new entry to the ledger."""
        entry = LedgerEntry(
            timestamp=datetime.now().isoformat(),
            original_path=str(original_path.absolute()),
            original_name=original_path.name,
            new_name=new_path.name,
            new_path=str(new_path.absolute()),
            model_used=model_used,
            confidence=confidence,
            content_hash=content_hash,
            extraction_method=extraction_method,
            pattern_id=pattern_id,
            reasoning=reasoning,
        )
        self._entries.append(entry)
        self._save()
        logger.info(f"Ledger: {original_path.name} -> {new_path.name}")
        return entry

    def get_entries(self, limit: Optional[int] = None) -> List[LedgerEntry]:
        """Get ledger entries, most recent first."""
        entries = sorted(self._entries, key=lambda e: e.timestamp, reverse=True)
        if limit:
            entries = entries[:limit]
        return entries

    def find_by_hash(self, content_hash: str) -> Optional[LedgerEntry]:
        """Find a previous entry with matching content hash."""
        for entry in self._entries:
            if entry.content_hash == content_hash:
                return entry
        return None

    def find_by_original_name(self, name: str) -> List[LedgerEntry]:
        """Find entries by original filename."""
        return [e for e in self._entries if e.original_name == name]

    def find_by_new_name(self, name: str) -> List[LedgerEntry]:
        """Find entries by new filename."""
        return [e for e in self._entries if e.new_name == name]

    def get_summary(self) -> dict:
        """Get a summary of ledger statistics."""
        if not self._entries:
            return {
                "total_processed": 0,
                "models_used": {},
                "extraction_methods": {},
                "average_confidence": 0,
                "patterns_applied": 0,
            }

        models = {}
        methods = {}
        total_confidence = 0
        patterns_applied = 0

        for entry in self._entries:
            models[entry.model_used] = models.get(entry.model_used, 0) + 1
            methods[entry.extraction_method] = methods.get(entry.extraction_method, 0) + 1
            total_confidence += entry.confidence
            if entry.pattern_id:
                patterns_applied += 1

        return {
            "total_processed": len(self._entries),
            "models_used": models,
            "extraction_methods": methods,
            "average_confidence": round(total_confidence / len(self._entries), 2),
            "patterns_applied": patterns_applied,
            "first_entry": self._entries[0].timestamp if self._entries else None,
            "last_entry": self._entries[-1].timestamp if self._entries else None,
        }

    def detect_manual_renames(self) -> List[dict]:
        """
        Detect files that were manually renamed after processing.
        Returns list of corrections for the learning system.
        """
        corrections = []

        for entry in self._entries:
            new_path = Path(entry.new_path)
            # Check if the renamed file still exists
            if not new_path.exists():
                # File was moved or renamed - check if any PDF exists in same directory
                parent = new_path.parent
                if parent.exists():
                    # Look for PDFs that might be the renamed version
                    for pdf in parent.glob("*.pdf"):
                        # Skip if it matches another ledger entry's new_path
                        if any(e.new_path == str(pdf) for e in self._entries):
                            continue
                        # This could be a manual rename - flag for review
                        corrections.append({
                            "original_entry": entry.to_dict(),
                            "potential_new_name": pdf.name,
                            "potential_new_path": str(pdf),
                        })

        return corrections


# Global ledger instance
_ledger: Optional[Ledger] = None


def get_ledger() -> Ledger:
    """Get or create the global ledger instance."""
    global _ledger
    if _ledger is None:
        _ledger = Ledger()
    return _ledger
