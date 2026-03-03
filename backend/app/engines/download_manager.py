"""
Module 5: Download Manager
Manages temp file storage for redacted outputs with auto-cleanup.
Provides job-based download endpoints.
Persists job metadata to disk so downloads survive server reloads.
"""

import os
import uuid
import time
import json
import logging
import threading
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Configurable
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "tmp_downloads")
EXPIRY_SECONDS = 3600  # 1 hour
METADATA_FILE = "jobs_metadata.json"


class DownloadManager:
    """Manages redacted output files for download with auto-cleanup.
    Persists job metadata to a JSON file so downloads survive server reloads.
    """

    def __init__(self, download_dir: str = DOWNLOAD_DIR, expiry_seconds: int = EXPIRY_SECONDS):
        self.download_dir = os.path.abspath(download_dir)
        self.expiry_seconds = expiry_seconds
        self.jobs: Dict[str, Dict] = {}
        self._metadata_path = os.path.join(self.download_dir, METADATA_FILE)

        os.makedirs(self.download_dir, exist_ok=True)

        # Restore persisted jobs
        self._load_metadata()

        # Start background cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        logger.info(f"DownloadManager initialized. Dir: {self.download_dir}, {len(self.jobs)} jobs restored")

    def save_file(
        self,
        file_bytes: bytes,
        original_filename: str,
        file_format: str,
        content_type: str,
        entity_count: int = 0,
        processing_time_ms: float = 0,
        audit_log: Optional[list] = None,
    ) -> str:
        """
        Save a redacted file and return a job_id for download.

        Returns:
            job_id string
        """
        job_id = str(uuid.uuid4())
        ext_map = {
            "png": ".png", "jpg": ".jpg", "jpeg": ".jpg",
            "pdf": ".pdf", "mp3": ".mp3", "wav": ".wav",
            "mp4": ".mp4", "mov": ".mov", "avi": ".avi",
        }
        ext = ext_map.get(file_format, f".{file_format}")

        # Construct download filename with correct extension
        base_name = os.path.splitext(original_filename)[0]
        download_filename = f"redacted_{base_name}{ext}"

        filename = f"{job_id}{ext}"
        filepath = os.path.join(self.download_dir, filename)

        with open(filepath, "wb") as f:
            f.write(file_bytes)

        self.jobs[job_id] = {
            "filepath": filepath,
            "filename": download_filename,
            "content_type": content_type,
            "file_size": len(file_bytes),
            "entity_count": entity_count,
            "processing_time_ms": processing_time_ms,
            "audit_log": audit_log or [],
            "created_at": time.time(),
        }

        # Persist to disk
        self._save_metadata()

        logger.info(f"Saved redacted file: {job_id} ({len(file_bytes)} bytes) -> {filepath}")
        return job_id

    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job metadata."""
        job = self.jobs.get(job_id)
        if job:
            # Verify file still exists
            if os.path.exists(job["filepath"]):
                return job
            else:
                # File was deleted, remove from jobs
                del self.jobs[job_id]
                self._save_metadata()
                return None
        return None

    def get_filepath(self, job_id: str) -> Optional[str]:
        """Get file path for a job."""
        job = self.get_job(job_id)
        if job:
            return job["filepath"]
        return None

    def _save_metadata(self):
        """Persist job metadata to JSON file."""
        try:
            # Don't persist audit_log to keep the file small
            slim_jobs = {}
            for jid, meta in self.jobs.items():
                slim_jobs[jid] = {
                    "filepath": meta["filepath"],
                    "filename": meta["filename"],
                    "content_type": meta["content_type"],
                    "file_size": meta["file_size"],
                    "entity_count": meta["entity_count"],
                    "processing_time_ms": meta["processing_time_ms"],
                    "created_at": meta["created_at"],
                }
            with open(self._metadata_path, "w") as f:
                json.dump(slim_jobs, f)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    def _load_metadata(self):
        """Load job metadata from JSON file."""
        if not os.path.exists(self._metadata_path):
            return

        try:
            with open(self._metadata_path, "r") as f:
                data = json.load(f)

            now = time.time()
            for jid, meta in data.items():
                # Skip expired jobs
                if now - meta.get("created_at", 0) > self.expiry_seconds:
                    continue
                # Skip jobs whose files are gone
                if not os.path.exists(meta.get("filepath", "")):
                    continue
                # Restore with empty audit_log
                meta["audit_log"] = []
                self.jobs[jid] = meta

            logger.info(f"Restored {len(self.jobs)} jobs from metadata")
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")

    def _cleanup_loop(self):
        """Background loop to clean up expired files."""
        while True:
            try:
                time.sleep(300)  # Check every 5 minutes
                self._cleanup_expired()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    def _cleanup_expired(self):
        """Remove files older than expiry_seconds."""
        now = time.time()
        expired_ids = []
        for job_id, meta in list(self.jobs.items()):
            if now - meta["created_at"] > self.expiry_seconds:
                filepath = meta["filepath"]
                if os.path.exists(filepath):
                    os.unlink(filepath)
                    logger.info(f"Cleaned up expired file: {job_id}")
                expired_ids.append(job_id)

        for jid in expired_ids:
            del self.jobs[jid]

        if expired_ids:
            self._save_metadata()
