"""LocalStorage behaviour: layout, cleanup, traversal guard."""

from uuid import uuid4

import pytest

from app.storage.local_storage import LocalStorage


async def test_save_writes_file_under_user_directory(
    test_storage: LocalStorage,
) -> None:
    user_id = uuid4()

    key = await test_storage.save(
        user_id=user_id,
        filename="my resume.PDF",
        content=b"%PDF-1.4 fake",
    )

    assert key.startswith(f"{user_id}/")
    assert key.endswith(".pdf")
    stored = test_storage.get_path(key)
    assert stored.exists()
    assert stored.read_bytes() == b"%PDF-1.4 fake"


async def test_save_ignores_unexpected_extensions(
    test_storage: LocalStorage,
) -> None:
    key = await test_storage.save(
        user_id=uuid4(),
        filename="payload.exe",
        content=b"whatever",
    )

    assert not key.endswith(".exe")


async def test_delete_removes_file_and_tolerates_missing(
    test_storage: LocalStorage,
) -> None:
    key = await test_storage.save(
        user_id=uuid4(),
        filename="cv.docx",
        content=b"bytes",
    )
    path = test_storage.get_path(key)

    await test_storage.delete(key)
    assert not path.exists()

    await test_storage.delete(key)  # second delete must not raise


def test_get_path_rejects_traversal(test_storage: LocalStorage) -> None:
    with pytest.raises(ValueError):
        test_storage.get_path("../../etc/passwd")


def test_storage_root_is_absolute(test_storage: LocalStorage) -> None:
    assert test_storage.base_dir.is_absolute()
