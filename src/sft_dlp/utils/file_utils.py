from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path


def compute_file_sha256(file_path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Compute SHA-256 digest for a file.

    Args:
        file_path: Absolute or relative path to an existing file.
        chunk_size: Number of bytes read per iteration.

    Returns:
        Hex-encoded SHA-256 digest.
    """
    digest = hashlib.sha256()
    with file_path.open("rb") as input_stream:
        while True:
            chunk = input_stream.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def guess_mime_type(file_path: Path) -> str:
    """Infer MIME type from file name/extension.

    Args:
        file_path: Path of the target file.

    Returns:
        MIME type or `application/octet-stream` if unknown.
    """
    guessed, _ = mimetypes.guess_type(str(file_path))
    return guessed or "application/octet-stream"


def normalize_user_path(path_value: Path) -> Path:
    """Normalize a user-supplied path into an absolute path.

    Args:
        path_value: Candidate path from user input.

    Returns:
        Resolved absolute path when validation succeeds.

    Raises:
        ValueError: If path contains traversal segments.
    """
    if ".." in path_value.parts:
        raise ValueError("Path traversal is not allowed.")
    return path_value.expanduser().resolve()


def validate_path_within_base(path_value: Path, *, base_dir: Path) -> Path:
    """Backward-compatible wrapper for legacy call sites.

    The application now supports selecting files/directories anywhere on the host
    filesystem, so `base_dir` is intentionally ignored.
    """
    _ = base_dir
    return normalize_user_path(path_value)
