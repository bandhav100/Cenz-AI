"""
Redaction Strategies Module.
Implements multiple privacy-preserving redaction techniques:
- Masking (████)
- Tag Replacement ([EMAIL], [PHONE], etc.)
- Anonymization (synthetic data via Faker)
- Hashing (SHA-256)
"""

import hashlib
import random
import string
from typing import List, Dict, Optional
from faker import Faker
import logging

logger = logging.getLogger(__name__)

fake = Faker()
Faker.seed(42)


class RedactionEngine:
    """
    Applies redaction strategies to detected PII entities.
    """

    MASK_CHAR = "█"

    # Faker generators mapped to entity types for anonymization
    FAKER_MAP = {
        "EMAIL": lambda: fake.email(),
        "PHONE": lambda: fake.phone_number(),
        "PERSON_NAME": lambda: fake.name(),
        "ORGANIZATION": lambda: fake.company(),
        "LOCATION": lambda: fake.city(),
        "DATE": lambda: fake.date(),
        "DATE_OF_BIRTH": lambda: fake.date_of_birth().isoformat(),
        "CREDIT_CARD": lambda: fake.credit_card_number(),
        "SSN": lambda: fake.ssn(),
        "IP_ADDRESS": lambda: fake.ipv4(),
        "URL": lambda: fake.url(),
        "AADHAAR": lambda: f"{random.randint(2000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}",
        "PAN_CARD": lambda: ''.join(random.choices(string.ascii_uppercase, k=5)) + ''.join(random.choices(string.digits, k=4)) + random.choice(string.ascii_uppercase),
        "PASSPORT": lambda: random.choice(string.ascii_uppercase) + str(random.randint(1000000, 9999999)),
        "ZIP_CODE": lambda: fake.zipcode(),
        "FINANCIAL": lambda: f"${random.randint(100, 99999):,.2f}",
        "NATIONALITY": lambda: fake.country(),
        "FACILITY": lambda: fake.street_address(),
        "TIME": lambda: fake.time(),
        "NUMBER": lambda: str(random.randint(1, 9999)),
    }

    def __init__(self):
        self._anonymization_cache = {}  # Cache for consistent anonymization

    def redact(self, text: str, entities: List[Dict], strategy: str = "mask") -> tuple:
        """
        Apply redaction to text based on detected entities.

        Args:
            text: Original text
            entities: List of detected entity dicts
            strategy: Redaction strategy (mask, tag_replace, anonymize, hash)

        Returns:
            Tuple of (redacted_text, entities_with_redacted_values)
        """
        if not entities:
            return text, entities

        strategy_fn = {
            "mask": self._mask,
            "tag_replace": self._tag_replace,
            "anonymize": self._anonymize,
            "hash": self._hash,
        }.get(strategy, self._mask)

        # Sort entities by start position in reverse
        sorted_entities = sorted(entities, key=lambda e: e["start"], reverse=True)

        redacted_text = text
        updated_entities = []

        for entity in sorted_entities:
            replacement = strategy_fn(entity)
            entity_copy = entity.copy()
            entity_copy["redacted_value"] = replacement

            start = entity["start"]
            end = entity["end"]
            redacted_text = redacted_text[:start] + replacement + redacted_text[end:]

            updated_entities.append(entity_copy)

        updated_entities.reverse()
        return redacted_text, updated_entities

    def _mask(self, entity: Dict) -> str:
        """Replace PII with block mask characters."""
        length = len(entity["value"])
        return self.MASK_CHAR * length

    def _tag_replace(self, entity: Dict) -> str:
        """Replace PII with semantic type tags."""
        return f"[{entity['entity_type']}]"

    def _anonymize(self, entity: Dict) -> str:
        """Replace PII with realistic synthetic data using Faker."""
        entity_type = entity["entity_type"]
        value = entity["value"]

        # Use cache for consistent anonymization (same input = same output)
        cache_key = f"{entity_type}:{value}"
        if cache_key in self._anonymization_cache:
            return self._anonymization_cache[cache_key]

        generator = self.FAKER_MAP.get(entity_type)
        if generator:
            try:
                synthetic = generator()
            except Exception:
                synthetic = f"[ANON_{entity_type}]"
        else:
            synthetic = f"[ANON_{entity_type}]"

        self._anonymization_cache[cache_key] = synthetic
        return synthetic

    def _hash(self, entity: Dict) -> str:
        """Replace PII with SHA-256 hash (truncated)."""
        value = entity["value"]
        hash_val = hashlib.sha256(value.encode()).hexdigest()[:16]
        return f"#{hash_val}#"

    def clear_cache(self):
        """Clear the anonymization cache."""
        self._anonymization_cache.clear()

    @staticmethod
    def get_strategies() -> List[Dict]:
        """Return available redaction strategies with descriptions."""
        return [
            {
                "id": "mask",
                "name": "Masking",
                "description": "Replaces characters with block symbols (████)",
                "icon": "🔒",
                "privacy_level": "high"
            },
            {
                "id": "tag_replace",
                "name": "Tag Replacement",
                "description": "Substitutes entities with semantic tags (e.g., [EMAIL])",
                "icon": "🏷️",
                "privacy_level": "high"
            },
            {
                "id": "anonymize",
                "name": "Anonymization",
                "description": "Replaces with realistic synthetic data",
                "icon": "🎭",
                "privacy_level": "medium"
            },
            {
                "id": "hash",
                "name": "Hashing",
                "description": "Generates irreversible cryptographic hashes",
                "icon": "🔐",
                "privacy_level": "highest"
            }
        ]
