"""
Storage service for managing files and model artifacts using local filesystem only.
"""

import logging
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for file and artifact storage (local filesystem)."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(settings.LOCAL_STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, object_name: str) -> Path:
        """Resolve object path safely within base_path."""
        object_path = self.base_path / object_name
        object_path.parent.mkdir(parents=True, exist_ok=True)
        return object_path

    async def upload_file(
        self,
        file_path: str,
        object_name: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """Copy a local file into storage directory."""
        src = Path(file_path)
        dest = self._resolve_path(object_name)
        dest.write_bytes(src.read_bytes())
        self.logger.info(f"File uploaded: {src} -> {dest}")
        return str(dest.relative_to(self.base_path))

    async def download_file(self, object_name: str, file_path: str) -> bool:
        """Copy a stored file to a target local path."""
        try:
            src = self._resolve_path(object_name)
            dest = Path(file_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(src.read_bytes())
            self.logger.info(f"File downloaded: {src} -> {dest}")
            return True
        except FileNotFoundError:
            self.logger.error(f"File not found: {object_name}")
            return False

    async def get_file_stream(self, object_name: str) -> BytesIO:
        """Return a BytesIO stream for the stored file."""
        path = self._resolve_path(object_name)
        return BytesIO(path.read_bytes())

    async def delete_file(self, object_name: str) -> bool:
        """Delete a stored file."""
        try:
            path = self._resolve_path(object_name)
            if path.exists():
                path.unlink()
                self.logger.info(f"File deleted: {object_name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting file {object_name}: {e}")
            return False

    async def list_files(self, prefix: str = "") -> list:
        """List files under prefix directory."""
        base = self.base_path / prefix if prefix else self.base_path
        if not base.exists():
            return []
        results = []
        for path in base.rglob("*"):
            if path.is_file():
                rel = path.relative_to(self.base_path)
                stat = path.stat()
                results.append(
                    {
                        "name": str(rel),
                        "size": stat.st_size,
                        "last_modified": stat.st_mtime,
                        "etag": None,
                    }
                )
        return results

    async def get_file_info(self, object_name: str) -> Optional[Dict[str, Any]]:
        """Get local file metadata."""
        path = self._resolve_path(object_name)
        if not path.exists():
            return None
        stat = path.stat()
        return {
            "name": object_name,
            "size": stat.st_size,
            "last_modified": stat.st_mtime,
            "etag": None,
            "content_type": None,
            "metadata": None,
        }

    async def get_model_file(self, model_path: str, format: str = "joblib") -> BytesIO:
        """Return the model file stream (no conversion)."""
        return await self.get_file_stream(model_path)

    async def delete_model_files(self, model_path: str) -> bool:
        """Delete all files under the model directory prefix."""
        try:
            model_dir = str(Path(model_path).parent)
            files = await self.list_files(prefix=model_dir)
            for file_info in files:
                await self.delete_file(file_info["name"])
            self.logger.info(f"Model files deleted: {model_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting model files {model_path}: {e}")
            return False
