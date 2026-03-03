"""
Entity Merger and Consolidation Module.
Merges entities from multiple detection engines (Regex, NLP, OCR),
resolves overlaps, and assigns unified confidence scores.
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class EntityMerger:
    """
    Consolidates entities from multiple detection sources.
    Resolves overlapping detections and merges confidence scores.
    """

    # Boost factor when multiple engines agree
    MULTI_SOURCE_BOOST = 0.10

    def merge(self, *entity_lists: List[Dict]) -> List[Dict]:
        """
        Merge entities from multiple detection engine outputs.

        Args:
            entity_lists: Variable number of entity lists from different engines

        Returns:
            Unified, deduplicated, overlap-resolved entity list
        """
        all_entities = []
        for elist in entity_lists:
            all_entities.extend(elist)

        if not all_entities:
            return []

        # Sort by start position
        all_entities.sort(key=lambda e: (e["start"], -e.get("confidence", 0)))

        # Merge overlapping entities
        merged = self._merge_overlaps(all_entities)

        # Assign final confidence scores
        for entity in merged:
            entity["confidence"] = min(entity.get("confidence", 0.5), 1.0)

        return sorted(merged, key=lambda e: e["start"])

    def _merge_overlaps(self, entities: List[Dict]) -> List[Dict]:
        """Merge overlapping entity detections."""
        if not entities:
            return []

        merged = []
        for entity in entities:
            was_merged = False
            for i, existing in enumerate(merged):
                overlap = self._calculate_overlap(entity, existing)
                if overlap > 0.5:
                    # Significant overlap — merge
                    merged[i] = self._merge_two(existing, entity)
                    was_merged = True
                    break
            if not was_merged:
                merged.append(entity.copy())

        return merged

    def _calculate_overlap(self, e1: Dict, e2: Dict) -> float:
        """Calculate the overlap ratio between two entities."""
        start = max(e1["start"], e2["start"])
        end = min(e1["end"], e2["end"])
        if start >= end:
            return 0.0

        overlap_len = end - start
        min_len = min(e1["end"] - e1["start"], e2["end"] - e2["start"])
        if min_len == 0:
            return 0.0

        return overlap_len / min_len

    def _merge_two(self, e1: Dict, e2: Dict) -> Dict:
        """Merge two overlapping entities into one."""
        # Use the entity with higher confidence as base
        if e1.get("confidence", 0) >= e2.get("confidence", 0):
            base, other = e1, e2
        else:
            base, other = e2, e1

        merged = base.copy()

        # Expand span to cover both
        merged["start"] = min(e1["start"], e2["start"])
        merged["end"] = max(e1["end"], e2["end"])

        # Boost confidence if from different sources
        if e1.get("source") != e2.get("source"):
            merged["confidence"] = min(
                base.get("confidence", 0.5) + self.MULTI_SOURCE_BOOST, 1.0
            )
            merged["source"] = f"{e1.get('source', 'unknown')}+{e2.get('source', 'unknown')}"

        return merged

    def get_stats(self, entities: List[Dict]) -> Dict:
        """Generate statistics from merged entity list."""
        stats = {
            "total": len(entities),
            "by_type": {},
            "by_source": {},
            "avg_confidence": 0.0,
            "high_confidence": 0,
            "medium_confidence": 0,
            "low_confidence": 0,
        }

        if not entities:
            return stats

        total_conf = 0
        for e in entities:
            etype = e.get("entity_type", "UNKNOWN")
            source = e.get("source", "unknown")
            conf = e.get("confidence", 0)

            stats["by_type"][etype] = stats["by_type"].get(etype, 0) + 1
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
            total_conf += conf

            if conf >= 0.8:
                stats["high_confidence"] += 1
            elif conf >= 0.5:
                stats["medium_confidence"] += 1
            else:
                stats["low_confidence"] += 1

        stats["avg_confidence"] = round(total_conf / len(entities), 3)
        return stats
