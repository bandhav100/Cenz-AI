"""
Module 4: Video Redaction Engine
Visual: EasyOCR text PII → black rects, MediaPipe face detection → Gaussian blur.
Audio: Whisper transcription → PII beep replacement (Module 3).
Merges redacted video frames + redacted audio → output MP4.
"""

import io
import logging
import time
import tempfile
import os
import math
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not installed")

MP_AVAILABLE = False
try:
    import mediapipe as mp
    # Test that solutions attribute exists
    _ = mp.solutions.face_detection
    MP_AVAILABLE = True
except (ImportError, AttributeError):
    logger.warning("MediaPipe not available")

MOVIEPY_AVAILABLE = False
try:
    from moviepy.editor import VideoFileClip, AudioFileClip, ImageSequenceClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    try:
        from moviepy import VideoFileClip, AudioFileClip, ImageSequenceClip
        MOVIEPY_AVAILABLE = True
    except ImportError:
        logger.warning("MoviePy not installed")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


class VideoRedactor:
    """Redacts PII from video: text overlay, face blur, audio beep."""

    def __init__(self):
        self.ocr_reader = None
        self.face_detector = None
        self.audio_redactor = None

        if EASYOCR_AVAILABLE:
            try:
                self.ocr_reader = easyocr.Reader(["en"], gpu=False)
            except Exception as e:
                logger.error(f"EasyOCR init failed: {e}")

        if MP_AVAILABLE:
            try:
                self.face_detector = mp.solutions.face_detection.FaceDetection(
                    model_selection=1, min_detection_confidence=0.5
                )
            except Exception as e:
                logger.error(f"MediaPipe init failed: {e}")

        try:
            from app.engines.audio_redactor import AudioRedactor
            self.audio_redactor = AudioRedactor()
        except Exception as e:
            logger.warning(f"AudioRedactor not available: {e}")

    def is_available(self) -> bool:
        return CV2_AVAILABLE and MOVIEPY_AVAILABLE

    def redact_video(
        self,
        video_bytes: bytes,
        filename: str,
        pii_pipeline_fn,
        strategy: str = "mask",
        frame_sample_rate: int = 1,  # Process every Nth frame for OCR
    ) -> Dict:
        """
        Full video redaction pipeline.

        Args:
            video_bytes: Raw video file bytes
            filename: Original filename
            pii_pipeline_fn: Callable(text) -> List[dict] for PII detection
            strategy: Redaction strategy
            frame_sample_rate: Process OCR every N frames (1=every frame)

        Returns:
            dict with redacted_video_bytes, audit_log, etc.
        """
        start_time = time.time()

        if not self.is_available():
            return {"error": "Video redaction dependencies not available"}

        # Save to temp file
        ext = os.path.splitext(filename)[1] if "." in filename else ".mp4"
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(video_bytes)
            video_path = tmp.name

        try:
            return self._process_video(
                video_path, pii_pipeline_fn, strategy, frame_sample_rate, start_time
            )
        finally:
            if os.path.exists(video_path):
                os.unlink(video_path)

    def _process_video(
        self, video_path: str, pii_pipeline_fn, strategy: str,
        frame_sample_rate: int, start_time: float
    ) -> Dict:
        """Core video processing pipeline."""
        # Open video
        clip = VideoFileClip(video_path)
        fps = clip.fps
        duration = clip.duration
        width, height = clip.size
        total_frames = int(duration * fps)

        visual_audit = []
        audio_audit = []

        # Process frames
        cap = cv2.VideoCapture(video_path)
        redacted_frames = []
        frame_idx = 0
        last_pii_regions = []  # Cache PII regions between sampled frames

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Run OCR + PII detection on sampled frames
            if frame_idx % max(1, int(fps * frame_sample_rate)) == 0:
                last_pii_regions = self._detect_frame_pii(
                    frame, frame_idx, pii_pipeline_fn, visual_audit
                )

            # Apply visual redactions to every frame
            frame = self._apply_visual_redactions(frame, last_pii_regions)

            # Face detection + blur on every frame
            frame = self._blur_faces(frame, frame_idx, visual_audit)

            # Convert BGR->RGB for MoviePy
            redacted_frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            frame_idx += 1

        cap.release()

        if not redacted_frames:
            return {"error": "No frames extracted from video"}

        # Reconstruct video from redacted frames
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as out_tmp:
            output_path = out_tmp.name

        try:
            redacted_clip = ImageSequenceClip(redacted_frames, fps=fps)

            # Process audio track if present
            audio_result = None
            if clip.audio is not None:
                audio_result = self._process_audio_track(
                    video_path, clip, pii_pipeline_fn, audio_audit
                )
                if audio_result and audio_result.get("redacted_audio_bytes"):
                    # Save redacted audio
                    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as audio_tmp:
                        audio_tmp.write(audio_result["redacted_audio_bytes"])
                        audio_path = audio_tmp.name

                    try:
                        audio_clip = AudioFileClip(audio_path)
                        # Trim audio to match video duration
                        if audio_clip.duration > redacted_clip.duration:
                            audio_clip = audio_clip.subclip(0, redacted_clip.duration)
                        redacted_clip = redacted_clip.set_audio(audio_clip)
                    except Exception as e:
                        logger.error(f"Audio merge failed: {e}")
                    finally:
                        os.unlink(audio_path)

            redacted_clip.write_videofile(
                output_path, codec="libx264", audio_codec="aac",
                logger=None, preset="ultrafast"
            )

            with open(output_path, "rb") as f:
                redacted_video_bytes = f.read()

            processing_time = (time.time() - start_time) * 1000

            return {
                "redacted_video_bytes": redacted_video_bytes,
                "format": "mp4",
                "visual_audit": visual_audit,
                "audio_audit": audio_audit,
                "audio_result": {
                    "original_transcript": audio_result.get("original_transcript", "") if audio_result else "",
                    "redacted_transcript": audio_result.get("redacted_transcript", "") if audio_result else "",
                },
                "entities_found": (audio_result.get("entities_found", []) if audio_result else []),
                "total_visual_redactions": len(visual_audit),
                "total_audio_redactions": len(audio_audit),
                "video_info": {
                    "fps": fps,
                    "duration_s": duration,
                    "width": width,
                    "height": height,
                    "total_frames": total_frames,
                },
                "processing_time_ms": processing_time,
            }
        finally:
            clip.close()
            if os.path.exists(output_path):
                os.unlink(output_path)

    def _detect_frame_pii(
        self, frame, frame_idx: int, pii_pipeline_fn, audit: List[Dict]
    ) -> List[Dict]:
        """Run OCR + PII detection on a single frame."""
        regions = []

        if not self.ocr_reader:
            return regions

        try:
            results = self.ocr_reader.readtext(frame)
            # Build text from OCR
            texts = [r[1] for r in results]
            full_text = " ".join(texts)

            if not full_text.strip():
                return regions

            entities = pii_pipeline_fn(full_text)

            # Map entities to bounding boxes
            offset = 0
            for bbox, text, conf in results:
                text_start = offset
                text_end = offset + len(text)
                offset = text_end + 1  # +1 for space

                for ent in entities:
                    ent_start = ent.get("start", 0)
                    ent_end = ent.get("end", 0)
                    if ent_start < text_end and ent_end > text_start:
                        region = {
                            "bbox": bbox,
                            "entity_type": ent.get("entity_type", "UNKNOWN"),
                            "value": ent.get("value", ""),
                            "confidence": ent.get("confidence", 0.0),
                        }
                        regions.append(region)
                        audit.append({
                            "frame": frame_idx,
                            "type": "text_pii",
                            "entity_type": ent.get("entity_type"),
                            "value": ent.get("value"),
                            "coordinates": [[int(p[0]), int(p[1])] for p in bbox],
                        })
        except Exception as e:
            logger.error(f"Frame {frame_idx} OCR error: {e}")

        return regions

    def _apply_visual_redactions(self, frame, regions: List[Dict]):
        """Draw black rectangles over PII text regions."""
        for region in regions:
            bbox = region["bbox"]
            pts = np.array([[int(p[0]), int(p[1])] for p in bbox], dtype=np.int32)
            cv2.fillPoly(frame, [pts], (0, 0, 0))
        return frame

    def _blur_faces(self, frame, frame_idx: int, audit: List[Dict]):
        """Detect and blur faces using MediaPipe."""
        if not self.face_detector:
            return frame

        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detector.process(rgb_frame)

            if results.detections:
                h, w, _ = frame.shape
                for detection in results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    x = int(bbox.xmin * w)
                    y = int(bbox.ymin * h)
                    bw = int(bbox.width * w)
                    bh = int(bbox.height * h)

                    # Clamp to frame bounds
                    x = max(0, x)
                    y = max(0, y)
                    bw = min(bw, w - x)
                    bh = min(bh, h - y)

                    if bw > 0 and bh > 0:
                        # Apply Gaussian blur
                        face_roi = frame[y:y+bh, x:x+bw]
                        blur_size = max(51, (min(bw, bh) // 3) | 1)
                        blurred = cv2.GaussianBlur(face_roi, (blur_size, blur_size), 30)
                        frame[y:y+bh, x:x+bw] = blurred

                        audit.append({
                            "frame": frame_idx,
                            "type": "face",
                            "coordinates": {"x": x, "y": y, "width": bw, "height": bh},
                            "confidence": float(detection.score[0]) if detection.score else 0.0,
                        })
        except Exception as e:
            logger.error(f"Face detection error on frame {frame_idx}: {e}")

        return frame

    def _process_audio_track(
        self, video_path: str, clip, pii_pipeline_fn, audit: List[Dict]
    ) -> Optional[Dict]:
        """Extract and redact audio track."""
        if not self.audio_redactor or not self.audio_redactor.is_available():
            return None

        try:
            # Extract audio to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_tmp:
                audio_path = audio_tmp.name

            clip.audio.write_audiofile(audio_path, logger=None)

            with open(audio_path, "rb") as f:
                audio_bytes = f.read()

            result = self.audio_redactor.redact_audio(
                audio_bytes, "audio.wav", pii_pipeline_fn, output_format="mp3"
            )

            audit.extend(result.get("audit_log", []))
            return result
        except Exception as e:
            logger.error(f"Audio track processing failed: {e}")
            return None
        finally:
            if os.path.exists(audio_path):
                os.unlink(audio_path)
