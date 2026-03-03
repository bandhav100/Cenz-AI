"""
Regex-based PII Detection Engine.
Detects structured identifiers: emails, phones, Aadhaar, credit cards, IPs, SSNs, dates, URLs.
"""

import re
from typing import List, Dict, Tuple

# Comprehensive PII regex patterns
PII_PATTERNS: Dict[str, List[Dict]] = {
    "EMAIL": [
        {
            "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "confidence": 0.95,
            "description": "Standard email address"
        }
    ],
    "PHONE": [
        {
            "pattern": r'\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b',
            "confidence": 0.85,
            "description": "US phone number"
        },
        {
            "pattern": r'\b(?:\+91[-.\s]?)?[6-9]\d{9}\b',
            "confidence": 0.90,
            "description": "Indian phone number"
        },
        {
            "pattern": r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b',
            "confidence": 0.75,
            "description": "International phone number"
        }
    ],
    "AADHAAR": [
        {
            "pattern": r'\b[2-9]\d{3}[-\s]?\d{4}[-\s]?\d{4}\b',
            "confidence": 0.90,
            "description": "Indian Aadhaar number"
        }
    ],
    "SSN": [
        {
            "pattern": r'\b(?!000|666|9\d{2})\d{3}[-\s]?(?!00)\d{2}[-\s]?(?!0000)\d{4}\b',
            "confidence": 0.88,
            "description": "US Social Security Number"
        }
    ],
    "CREDIT_CARD": [
        {
            "pattern": r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b',
            "confidence": 0.92,
            "description": "Credit card number (Visa, MC, Amex, Discover)"
        },
        {
            "pattern": r'\b\d{4}[-\s]\d{4}[-\s]\d{4}[-\s]\d{4}\b',
            "confidence": 0.85,
            "description": "Credit card with separators"
        }
    ],
    "IP_ADDRESS": [
        {
            "pattern": r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b',
            "confidence": 0.90,
            "description": "IPv4 address"
        },
        {
            "pattern": r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',
            "confidence": 0.92,
            "description": "IPv6 address"
        }
    ],
    "DATE_OF_BIRTH": [
        {
            "pattern": r'\b(?:0[1-9]|[12]\d|3[01])[-/](?:0[1-9]|1[0-2])[-/](?:19|20)\d{2}\b',
            "confidence": 0.70,
            "description": "Date DD/MM/YYYY or DD-MM-YYYY"
        },
        {
            "pattern": r'\b(?:19|20)\d{2}[-/](?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])\b',
            "confidence": 0.70,
            "description": "Date YYYY/MM/DD or YYYY-MM-DD"
        }
    ],
    "URL": [
        {
            "pattern": r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)',
            "confidence": 0.80,
            "description": "URL/Web address"
        }
    ],
    "PAN_CARD": [
        {
            "pattern": r'\b[A-Z]{5}\d{4}[A-Z]\b',
            "confidence": 0.85,
            "description": "Indian PAN card number"
        }
    ],
    "PASSPORT": [
        {
            "pattern": r'\b[A-Z][1-9]\d{7}\b',
            "confidence": 0.70,
            "description": "Indian Passport number"
        }
    ],
    "ZIP_CODE": [
        {
            "pattern": r'\b\d{5}(?:-\d{4})?\b',
            "confidence": 0.60,
            "description": "US ZIP code"
        },
        {
            "pattern": r'\b\d{6}\b',
            "confidence": 0.50,
            "description": "Indian PIN code"
        }
    ],
    "PERSON_NAME": [
        {
            "pattern": r'(?:(?:my name is|i am|this is|i\'m|call me|name:\s*|name\s*[-–]\s*)\s*)([A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+)*)',
            "confidence": 0.80,
            "description": "Name from contextual phrase"
        },
        {
            "pattern": r'(?:(?:hi|hello|hey|dear)\s+(?:this is|i am|i\'m)\s+)([A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+)*)',
            "confidence": 0.80,
            "description": "Name from greeting phrase"
        },
    ],
    "ADDRESS": [
        {
            "pattern": r'(?:(?:i live in|i live at|address is|address:\s*|located at|residing at|resident of|live in|stay at|stay in)\s+)(.+?)(?:\.|,\s*(?:phone|email|contact|my)|$)',
            "confidence": 0.78,
            "description": "Address from contextual phrase"
        },
        {
            "pattern": r'\b\d{1,5}[-/]\d{1,5}(?:[-/]\d{1,5})?\s+[A-Za-z].*?(?:road|street|st|avenue|ave|lane|ln|nagar|colony|sector|block|cross|main|layout|puram|pet|peta|abad)\b',
            "confidence": 0.72,
            "description": "Street address with number and road type"
        },
    ],
}


class RegexEngine:
    """
    Deterministic regex-based PII detection engine.
    Provides high precision for structured identifiers.
    """

    def __init__(self, custom_patterns: Dict = None):
        self.patterns = {**PII_PATTERNS}
        if custom_patterns:
            self.patterns.update(custom_patterns)
        self._compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, List[Dict]]:
        """Pre-compile all regex patterns for performance."""
        compiled = {}
        for entity_type, pattern_list in self.patterns.items():
            compiled[entity_type] = []
            for p in pattern_list:
                try:
                    compiled[entity_type].append({
                        "compiled": re.compile(p["pattern"], re.IGNORECASE),
                        "confidence": p["confidence"],
                        "description": p["description"]
                    })
                except re.error:
                    continue
        return compiled

    def detect(self, text: str, entity_types: List[str] = None) -> List[Dict]:
        """
        Detect PII entities in text using regex patterns.
        
        Args:
            text: Input text to scan
            entity_types: Optional list of specific entity types to detect
            
        Returns:
            List of detected entity dictionaries
        """
        entities = []
        target_types = entity_types or list(self._compiled_patterns.keys())

        for entity_type in target_types:
            if entity_type not in self._compiled_patterns:
                continue
            for pattern_info in self._compiled_patterns[entity_type]:
                for match in pattern_info["compiled"].finditer(text):
                    # Use capture group if available, else full match
                    if match.lastindex and match.lastindex >= 1:
                        value = match.group(1).strip()
                        # Compute the actual start/end for the captured group
                        start = match.start(1)
                        end = match.end(1)
                    else:
                        value = match.group()
                        start = match.start()
                        end = match.end()

                    if not value:
                        continue

                    entities.append({
                        "entity_type": entity_type,
                        "value": value,
                        "start": start,
                        "end": end,
                        "confidence": pattern_info["confidence"],
                        "source": "regex",
                        "description": pattern_info["description"]
                    })

        # Remove duplicates and overlapping matches
        entities = self._resolve_overlaps(entities)
        return entities

    def _resolve_overlaps(self, entities: List[Dict]) -> List[Dict]:
        """Remove overlapping entity detections, keeping higher confidence ones."""
        if not entities:
            return entities

        # Sort by start position, then by confidence (descending)
        entities.sort(key=lambda x: (x["start"], -x["confidence"]))

        resolved = []
        for entity in entities:
            overlap = False
            for existing in resolved:
                if (entity["start"] < existing["end"] and entity["end"] > existing["start"]):
                    # There's an overlap — keep the higher confidence one
                    if entity["confidence"] > existing["confidence"]:
                        resolved.remove(existing)
                        resolved.append(entity)
                    overlap = True
                    break
            if not overlap:
                resolved.append(entity)

        return sorted(resolved, key=lambda x: x["start"])

    def get_supported_types(self) -> List[str]:
        """Return list of supported entity types."""
        return list(self.patterns.keys())
