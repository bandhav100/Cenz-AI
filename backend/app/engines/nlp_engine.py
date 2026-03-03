"""
NLP-based PII Detection Engine.
Uses spaCy Named Entity Recognition to detect contextual entities
such as person names, organizations, locations, dates, etc.
"""

from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Entity type mapping from spaCy labels to our PII types
SPACY_TO_PII_MAP = {
    "PERSON": "PERSON_NAME",
    "ORG": "ORGANIZATION",
    "GPE": "LOCATION",
    "LOC": "LOCATION",
    "DATE": "DATE",
    "TIME": "TIME",
    "MONEY": "FINANCIAL",
    "CARDINAL": "NUMBER",
    "NORP": "NATIONALITY",
    "FAC": "FACILITY",
    "EVENT": "EVENT",
    "WORK_OF_ART": "WORK_OF_ART",
    "PRODUCT": "PRODUCT",
}

# Confidence scores for each entity type from NLP
NLP_CONFIDENCE = {
    "PERSON_NAME": 0.85,
    "ORGANIZATION": 0.80,
    "LOCATION": 0.82,
    "DATE": 0.75,
    "TIME": 0.70,
    "FINANCIAL": 0.78,
    "NUMBER": 0.50,
    "NATIONALITY": 0.72,
    "FACILITY": 0.68,
    "EVENT": 0.65,
    "WORK_OF_ART": 0.60,
    "PRODUCT": 0.62,
}

# Entity types considered PII-relevant (filter out low-value ones)
PII_RELEVANT_TYPES = {
    "PERSON_NAME", "ORGANIZATION", "LOCATION", "DATE",
    "FINANCIAL", "NATIONALITY", "FACILITY"
}


class NLPEngine:
    """
    NLP-based PII detection using spaCy Named Entity Recognition.
    Provides high recall for contextual entities.
    """

    def __init__(self, model_name: str = "en_core_web_sm"):
        self.model_name = model_name
        self.nlp = None
        self._loaded = False

    def load(self):
        """Load the spaCy model."""
        if self._loaded:
            return

        try:
            import spacy
            self.nlp = spacy.load(self.model_name)
            self._loaded = True
            logger.info(f"NLP engine loaded: {self.model_name}")
        except OSError:
            logger.warning(f"spaCy model '{self.model_name}' not found. Attempting download...")
            try:
                import spacy.cli
                spacy.cli.download(self.model_name)
                import spacy
                self.nlp = spacy.load(self.model_name)
                self._loaded = True
                logger.info(f"NLP engine loaded after download: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to load spaCy model: {e}")
                self._loaded = False
        except Exception as e:
            logger.error(f"NLP engine initialization failed: {e}")
            self._loaded = False

    def is_available(self) -> bool:
        """Check if the NLP engine is loaded and available."""
        return self._loaded and self.nlp is not None

    def detect(self, text: str, entity_types: List[str] = None, pii_only: bool = True) -> List[Dict]:
        """
        Detect entities using NLP/NER.

        Args:
            text: Input text to analyze
            entity_types: Optional filter for specific entity types
            pii_only: If True, only return PII-relevant entity types

        Returns:
            List of detected entity dictionaries
        """
        if not self.is_available():
            self.load()
            if not self.is_available():
                logger.warning("NLP engine not available, returning empty results")
                return []

        try:
            doc = self.nlp(text)
        except Exception as e:
            logger.error(f"NLP processing error: {e}")
            return []

        entities = []
        for ent in doc.ents:
            pii_type = SPACY_TO_PII_MAP.get(ent.label_)
            if not pii_type:
                continue

            if pii_only and pii_type not in PII_RELEVANT_TYPES:
                continue

            if entity_types and pii_type not in entity_types:
                continue

            # Skip very short or numeric-only entities
            if len(ent.text.strip()) < 2:
                continue

            confidence = NLP_CONFIDENCE.get(pii_type, 0.60)

            entities.append({
                "entity_type": pii_type,
                "value": ent.text,
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": confidence,
                "source": "nlp",
                "spacy_label": ent.label_,
                "description": f"NER-detected {pii_type}"
            })

        return self._deduplicate(entities)

    def _deduplicate(self, entities: List[Dict]) -> List[Dict]:
        """Remove exact duplicate detections."""
        seen = set()
        unique = []
        for e in entities:
            key = (e["entity_type"], e["start"], e["end"])
            if key not in seen:
                seen.add(key)
                unique.append(e)
        return unique

    def get_supported_types(self) -> List[str]:
        """Return list of NLP-detectable PII types."""
        return list(PII_RELEVANT_TYPES)
