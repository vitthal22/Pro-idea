"""Storage abstraction.

Business logic depends on this protocol only. The local filesystem backs
the MVP; S3/R2 can be added later as another implementation selected by
``STORAGE_BACKEND`` — no service or router changes.
"""

from pathlib import Path
from typing import Protocol
from uuid import UUID


class Storage(Protocol):
    """Contract for storing uploaded files."""

    async def save(self, *, user_id: UUID, filename: str, content: bytes) -> str:
        """Persist bytes and return a storage key (path relative to the root)."""
        ...

    async def delete(self, path: str) -> None:
        """Delete the stored object; missing objects are not an error."""
        ...

    def get_path(self, path: str) -> Path:
        """Return the local filesystem path for a storage key."""
        ...
