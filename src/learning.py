"""Learning system for pattern recognition and user corrections."""

import json
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple
from dataclasses import dataclass, asdict
from collections import Counter

from .config import PATTERNS_FILE, CORRECTIONS_FILE

logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """A learned document pattern."""

    pattern_id: str
    signature_keywords: List[str]  # Key phrases that identify this pattern
    description_template: str  # Template for naming (e.g., "Electric_Bill_{month}")
    source_examples: List[str]  # Original filenames that matched this pattern
    times_applied: int
    confidence_avg: float
    created_at: str
    last_used: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Pattern":
        return cls(**data)


@dataclass
class Correction:
    """A user correction to learn from."""

    correction_id: str
    original_name: str  # What the system suggested
    corrected_name: str  # What the user renamed it to
    content_hash: str
    keywords_in_content: List[str]  # Extracted keywords for matching
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Correction":
        return cls(**data)


class LearningSystem:
    """Manages pattern recognition and learning from corrections."""

    def __init__(
        self,
        patterns_path: Path = PATTERNS_FILE,
        corrections_path: Path = CORRECTIONS_FILE,
    ):
        self.patterns_path = patterns_path
        self.corrections_path = corrections_path
        self._patterns: List[Pattern] = []
        self._corrections: List[Correction] = []
        self._load()

    def _load(self) -> None:
        """Load patterns and corrections from disk."""
        # Load patterns
        if self.patterns_path.exists():
            try:
                with open(self.patterns_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._patterns = [Pattern.from_dict(p) for p in data.get("patterns", [])]
                logger.debug(f"Loaded {len(self._patterns)} patterns")
            except Exception as e:
                logger.error(f"Failed to load patterns: {e}")
                self._patterns = []

        # Load corrections
        if self.corrections_path.exists():
            try:
                with open(self.corrections_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._corrections = [Correction.from_dict(c) for c in data.get("corrections", [])]
                logger.debug(f"Loaded {len(self._corrections)} corrections")
            except Exception as e:
                logger.error(f"Failed to load corrections: {e}")
                self._corrections = []

    def _save_patterns(self) -> None:
        """Save patterns to disk."""
        data = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "patterns": [p.to_dict() for p in self._patterns],
        }
        with open(self.patterns_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _save_corrections(self) -> None:
        """Save corrections to disk."""
        data = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "corrections": [c.to_dict() for c in self._corrections],
        }
        with open(self.corrections_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract significant keywords from text for pattern matching."""
        # Normalize and tokenize
        text = text.lower()
        words = re.findall(r'\b[a-z]{3,}\b', text)

        # Count word frequencies
        word_counts = Counter(words)

        # Filter out very common words
        stopwords = {
            'the', 'and', 'for', 'that', 'this', 'with', 'from', 'have', 'has',
            'are', 'was', 'were', 'been', 'being', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'please',
            'page', 'date', 'amount', 'total', 'number', 'account', 'name',
        }

        # Get top meaningful keywords
        keywords = [
            word for word, count in word_counts.most_common(50)
            if word not in stopwords and count >= 1
        ][:20]

        return keywords

    def _compute_signature(self, text: str) -> List[str]:
        """Compute a signature for pattern matching."""
        # Look for distinctive identifiers
        patterns_to_find = [
            # Company/organization names (often in headers)
            r'^([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,3})',
            # Account numbers
            r'account[:\s#]*(\d{4,})',
            # Document types
            r'\b(invoice|statement|bill|receipt|notice|letter|report)\b',
        ]

        signatures = []
        for pattern in patterns_to_find:
            matches = re.findall(pattern, text[:2000], re.IGNORECASE | re.MULTILINE)
            signatures.extend([m.lower() if isinstance(m, str) else m[0].lower() for m in matches[:3]])

        return list(set(signatures))[:10]

    def find_matching_pattern(self, text: str, content_hash: str) -> Optional[Tuple[Pattern, float]]:
        """
        Find a pattern that matches the given document text.

        Returns (Pattern, match_score) or None if no good match.
        """
        # First check corrections (higher priority)
        for correction in self._corrections:
            if correction.content_hash == content_hash:
                # Exact match from correction
                logger.info(f"Found exact correction match: {correction.corrected_name}")
                return None  # Return None to trigger special handling

        if not self._patterns:
            return None

        keywords = self._extract_keywords(text)
        signatures = self._compute_signature(text)

        best_match = None
        best_score = 0.0

        for pattern in self._patterns:
            # Score based on keyword overlap
            keyword_overlap = len(set(keywords) & set(pattern.signature_keywords))
            if not pattern.signature_keywords:
                continue

            score = keyword_overlap / len(pattern.signature_keywords)

            # Boost for frequently applied patterns
            if pattern.times_applied > 5:
                score *= 1.1

            if score > best_score and score >= 0.5:  # Minimum 50% match
                best_score = score
                best_match = pattern

        if best_match:
            logger.info(f"Found pattern match: {best_match.pattern_id} (score: {best_score:.2f})")
            return best_match, best_score

        return None

    def get_correction_suggestion(self, content_hash: str) -> Optional[str]:
        """Get a corrected name if this content was previously corrected."""
        for correction in self._corrections:
            if correction.content_hash == content_hash:
                return correction.corrected_name
        return None

    def learn_from_success(
        self,
        text: str,
        suggested_name: str,
        confidence: float,
        content_hash: str,
    ) -> Optional[str]:
        """
        Learn from a successful naming to create/update patterns.
        Returns pattern_id if a pattern was created/updated.
        """
        keywords = self._extract_keywords(text)

        if not keywords:
            return None

        # Check if this matches an existing pattern
        for pattern in self._patterns:
            keyword_overlap = len(set(keywords) & set(pattern.signature_keywords))
            if keyword_overlap >= len(pattern.signature_keywords) * 0.6:
                # Update existing pattern
                pattern.times_applied += 1
                pattern.confidence_avg = (
                    (pattern.confidence_avg * (pattern.times_applied - 1) + confidence)
                    / pattern.times_applied
                )
                pattern.last_used = datetime.now().isoformat()
                if suggested_name not in pattern.source_examples:
                    pattern.source_examples.append(suggested_name)
                    pattern.source_examples = pattern.source_examples[-10:]  # Keep last 10
                self._save_patterns()
                logger.debug(f"Updated pattern {pattern.pattern_id}")
                return pattern.pattern_id

        # Create new pattern if confidence is high enough
        if confidence >= 0.75 and len(keywords) >= 3:
            pattern_id = f"pat_{datetime.now().strftime('%Y%m%d%H%M%S')}_{content_hash[:6]}"
            new_pattern = Pattern(
                pattern_id=pattern_id,
                signature_keywords=keywords[:15],
                description_template=suggested_name,
                source_examples=[suggested_name],
                times_applied=1,
                confidence_avg=confidence,
                created_at=datetime.now().isoformat(),
                last_used=datetime.now().isoformat(),
            )
            self._patterns.append(new_pattern)
            self._save_patterns()
            logger.info(f"Created new pattern: {pattern_id}")
            return pattern_id

        return None

    def add_correction(
        self,
        original_name: str,
        corrected_name: str,
        content_hash: str,
        text: str,
    ) -> str:
        """Add a user correction to learn from."""
        keywords = self._extract_keywords(text)

        correction_id = f"cor_{datetime.now().strftime('%Y%m%d%H%M%S')}_{content_hash[:6]}"
        correction = Correction(
            correction_id=correction_id,
            original_name=original_name,
            corrected_name=corrected_name,
            content_hash=content_hash,
            keywords_in_content=keywords[:15],
            created_at=datetime.now().isoformat(),
        )
        self._corrections.append(correction)
        self._save_corrections()
        logger.info(f"Added correction: {original_name} -> {corrected_name}")
        return correction_id

    def get_stats(self) -> dict:
        """Get learning system statistics."""
        return {
            "total_patterns": len(self._patterns),
            "total_corrections": len(self._corrections),
            "most_used_patterns": sorted(
                [(p.pattern_id, p.times_applied) for p in self._patterns],
                key=lambda x: x[1],
                reverse=True,
            )[:5],
        }


# Global instance
_learning_system: Optional[LearningSystem] = None


def get_learning_system() -> LearningSystem:
    """Get or create the global learning system instance."""
    global _learning_system
    if _learning_system is None:
        _learning_system = LearningSystem()
    return _learning_system
