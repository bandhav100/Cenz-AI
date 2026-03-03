"""
Module 3: Audio Redaction Engine
Transcribes audio with Whisper (word-level timestamps),
detects PII, replaces PII segments with 1kHz beep tones.
Returns redacted audio + transcript JSON.
"""

import io
import logging
import time
import tempfile
import os
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Whisper not installed")

try:
    from pydub import AudioSegment
    from pydub.generators import Sine
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning("pydub not installed")


class AudioRedactor:
    """Redacts PII from audio using Whisper transcription + beep overlay."""

    def __init__(self, model_size: str = "base"):
        self.model = None
        self.model_size = model_size
        if WHISPER_AVAILABLE:
            try:
                self.model = whisper.load_model(model_size)
                logger.info(f"Whisper model '{model_size}' loaded for AudioRedactor")
            except Exception as e:
                logger.error(f"Whisper model load failed: {e}")

    def is_available(self) -> bool:
        return WHISPER_AVAILABLE and PYDUB_AVAILABLE and self.model is not None

    def redact_audio(
        self,
        audio_bytes: bytes,
        filename: str,
        pii_pipeline_fn,
        strategy: str = "mask",
        output_format: str = "mp3"
    ) -> Dict:
        """
        Full audio redaction pipeline.

        Args:
            audio_bytes: Raw audio file bytes
            filename: Original filename (for format detection)
            pii_pipeline_fn: Callable(text) -> List[dict] for PII detection
            strategy: Redaction strategy
            output_format: Output format (mp3 or wav)

        Returns:
            dict with redacted_audio_bytes, transcript, audit_log, etc.
        """
        start_time = time.time()

        if not self.is_available():
            return {"error": "Audio redaction dependencies not available"}

        # Save audio to temp file for Whisper
        ext = os.path.splitext(filename)[1] if "." in filename else ".mp3"
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            # Transcribe with word-level timestamps
            transcript_result = self.model.transcribe(
                tmp_path,
                word_timestamps=True,
                language="en"
            )

            # Extract word-level timestamps
            words_with_ts = []
            for segment in transcript_result.get("segments", []):
                for word_info in segment.get("words", []):
                    words_with_ts.append({
                        "word": word_info["word"].strip(),
                        "start": word_info["start"],
                        "end": word_info["end"],
                    })

            # Build full transcript text
            full_text = transcript_result.get("text", "").strip()

            # Run PII detection
            pii_entities = pii_pipeline_fn(full_text)

            # Map PII entities to timestamps
            pii_segments = self._map_pii_to_timestamps(pii_entities, words_with_ts, full_text)

            # Merge overlapping segments
            merged_segments = self._merge_overlapping(pii_segments)

            # Load audio with pydub
            audio = AudioSegment.from_file(tmp_path)

            # Replace PII segments with beep tones
            redacted_audio = self._apply_beeps(audio, merged_segments)

            # Export
            buf = io.BytesIO()
            redacted_audio.export(buf, format=output_format)

            # Build redacted transcript
            redacted_text = self._build_redacted_transcript(full_text, pii_entities)

            processing_time = (time.time() - start_time) * 1000

            audit_log = []
            for seg in merged_segments:
                audit_log.append({
                    "entity_type": seg["entity_type"],
                    "value": seg["value"],
                    "confidence": seg.get("confidence", 0.0),
                    "start_ms": int(seg["start_ms"]),
                    "end_ms": int(seg["end_ms"]),
                    "duration_ms": int(seg["end_ms"] - seg["start_ms"]),
                })

            return {
                "redacted_audio_bytes": buf.getvalue(),
                "format": output_format,
                "original_transcript": full_text,
                "redacted_transcript": redacted_text,
                "audit_log": audit_log,
                "entities_found": pii_entities,
                "total_entities": len(pii_entities),
                "total_beep_segments": len(merged_segments),
                "audio_duration_ms": len(audio),
                "processing_time_ms": processing_time,
            }

        finally:
            os.unlink(tmp_path)

    def _map_pii_to_timestamps(
        self, entities: List[Dict], words: List[Dict], full_text: str
    ) -> List[Dict]:
        """Map PII entities to audio timestamps using word positions."""
        segments = []

        for entity in entities:
            ent_value = entity.get("value", "")
            ent_start = entity.get("start", 0)
            ent_end = entity.get("end", 0)

            # Find words whose text offsets overlap with the entity
            matched_words = []
            current_offset = 0
            for w in words:
                word_text = w["word"]
                # Find word position in full text
                word_pos = full_text.find(word_text, current_offset)
                if word_pos == -1:
                    continue
                word_end = word_pos + len(word_text)
                current_offset = word_end

                # Check overlap
                if word_pos < ent_end and word_end > ent_start:
                    matched_words.append(w)

            if matched_words:
                start_ms = matched_words[0]["start"] * 1000
                end_ms = matched_words[-1]["end"] * 1000
                segments.append({
                    "entity_type": entity.get("entity_type", "UNKNOWN"),
                    "value": ent_value,
                    "confidence": entity.get("confidence", 0.0),
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                })

        return segments

    def _merge_overlapping(self, segments: List[Dict]) -> List[Dict]:
        """Merge overlapping PII segments."""
        if not segments:
            return []

        sorted_segs = sorted(segments, key=lambda s: s["start_ms"])
        merged = [sorted_segs[0].copy()]

        for seg in sorted_segs[1:]:
            last = merged[-1]
            if seg["start_ms"] <= last["end_ms"]:
                last["end_ms"] = max(last["end_ms"], seg["end_ms"])
                last["value"] += f", {seg['value']}"
                last["entity_type"] = f"{last['entity_type']},{seg['entity_type']}"
            else:
                merged.append(seg.copy())

        return merged

    def _apply_beeps(self, audio: "AudioSegment", segments: List[Dict]) -> "AudioSegment":
        """Replace PII segments with 1kHz beep tones."""
        if not segments:
            return audio

        result = AudioSegment.empty()
        prev_end = 0

        for seg in segments:
            start_ms = int(seg["start_ms"])
            end_ms = int(seg["end_ms"])
            duration = end_ms - start_ms

            if duration <= 0:
                continue

            # Add non-PII audio before this segment
            if start_ms > prev_end:
                result += audio[prev_end:start_ms]

            # Generate beep tone
            beep = Sine(1000).to_audio_segment(duration=duration)
            # Match volume to original
            original_chunk = audio[start_ms:end_ms]
            if len(original_chunk) > 0 and original_chunk.dBFS > -60:
                beep = beep - max(0, beep.dBFS - original_chunk.dBFS)
            else:
                beep = beep - 10  # Reduce volume for silence

            result += beep
            prev_end = end_ms

        # Add remaining audio
        if prev_end < len(audio):
            result += audio[prev_end:]

        return result

    def _build_redacted_transcript(self, text: str, entities: List[Dict]) -> str:
        """Build transcript with [REDACTED] tags."""
        sorted_ents = sorted(entities, key=lambda e: e.get("start", 0), reverse=True)
        result = text
        for ent in sorted_ents:
            start = ent.get("start", 0)
            end = ent.get("end", 0)
            label = ent.get("entity_type", "PII")
            result = result[:start] + f"[{label}]" + result[end:]
        return result
