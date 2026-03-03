"""
Verification Engine.
Post-redaction scanning to ensure no residual PII remains.
Re-scans redacted output and flags any remaining sensitive data.
"""

from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class VerificationEngine:
    """
    Post-redaction verification module.
    Re-scans redacted output to detect residual PII.
    """

    def __init__(self, regex_engine, nlp_engine=None):
        self.regex_engine = regex_engine
        self.nlp_engine = nlp_engine

    def verify(self, redacted_text: str, max_retries: int = 2) -> Dict:
        """
        Verify that redacted text contains no residual PII.

        Args:
            redacted_text: The redacted text to verify
            max_retries: Maximum verification attempts

        Returns:
            Verification result dictionary
        """
        result = {
            "passed": True,
            "residual_entities": [],
            "scan_count": 0,
            "confidence": 1.0
        }

        for attempt in range(max_retries):
            result["scan_count"] = attempt + 1

            # Regex scan
            regex_entities = self.regex_engine.detect(redacted_text)

            # Filter out false positives from redaction artifacts
            real_entities = [
                e for e in regex_entities
                if not self._is_redaction_artifact(e, redacted_text)
            ]

            # NLP scan if available
            nlp_entities = []
            if self.nlp_engine and self.nlp_engine.is_available():
                nlp_entities = self.nlp_engine.detect(redacted_text)
                nlp_entities = [
                    e for e in nlp_entities
                    if not self._is_redaction_artifact(e, redacted_text)
                ]

            all_residual = real_entities + nlp_entities

            if not all_residual:
                result["passed"] = True
                result["confidence"] = 1.0
                break
            else:
                result["residual_entities"] = all_residual
                result["passed"] = False
                result["confidence"] = max(0, 1.0 - (len(all_residual) * 0.1))

        return result

    def _is_redaction_artifact(self, entity: Dict, text: str) -> bool:
        """
        Check if a detected entity is actually a redaction artifact
        (e.g., [EMAIL], ████, hash values) rather than real PII.
        """
        value = entity.get("value", "")

        # Check if it's a tag replacement
        if value.startswith("[") and value.endswith("]"):
            return True

        # Check if it's mask characters
        if all(c == "█" for c in value):
            return True

        # Check if it's a hash artifact
        if value.startswith("#") and value.endswith("#"):
            return True

        # Check if it's inside a redaction tag
        start = entity.get("start", 0)
        end = entity.get("end", 0)
        context_start = max(0, start - 5)
        context_end = min(len(text), end + 5)
        context = text[context_start:context_end]

        if "[" in context and "]" in context:
            return True

        return False

    def quick_verify(self, redacted_text: str) -> bool:
        """Quick boolean pass/fail verification."""
        result = self.verify(redacted_text, max_retries=1)
        return result["passed"]
