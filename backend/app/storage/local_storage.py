"""Local filesystem storage.

Files live under ``UPLOAD_DIR`` as ``{user_id}/{uuid}{ext}``. The root is
resolved relative to the backend package (never the process cwd), so local
and container runs produce the same layout.
"""

import asyncio
from pathlib import Path
from uuid import UUID, uuid4

from app.config import settings

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SAFE_EXTENSIONS = frozenset({".pdf", ".docx"})


def _default_base_dir() -> Path:
    """Resolve ``UPLOAD_DIR`` against the backend root, not the cwd."""
    configured = Path(settings.upload_dir)
    if not configured.is_absolute():
        configured = BACKEND_ROOT / configured
    return configured.resolve()


class LocalStorage:
    """Filesystem-backed ``Storage`` implementation."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self._base_dir = Path(base_dir).resolve() if base_dir else _default_base_dir()

    @property
    def base_dir(self) -> Path:
        """Absolute upload root (useful for diagnostics and tests)."""
        return self._base_dir

    async def save(self, *, user_id: UUID, filename: str, content: bytes) -> str:
        """Write the file and return its key relative to the upload root."""
        suffix = Path(filename).suffix.lower()
        if suffix not in SAFE_EXTENSIONS:
            suffix = ""
        key = f"{user_id}/{uuid4().hex}{suffix}"
        await asyncio.to_thread(self._write, self.get_path(key), content)
        return key

    async def delete(self, path: str) -> None:
        """Remove the file if it exists."""
        await asyncio.to_thread(self.get_path(path).unlink, missing_ok=True)

    def get_path(self, path: str) -> Path:
        """Resolve a key inside the upload root, rejecting traversal."""
        target = (self._base_dir / path).resolve()
        if not target.is_relative_to(self._base_dir):
            raise ValueError(f"Storage key escapes the upload root: {path!r}")
        return target

    @staticmethod
    def _write(target: Path, content: bytes) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
