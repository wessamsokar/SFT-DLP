from __future__ import annotations

import hashlib
import mimetypes
import os
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


def validate_path_within_base(path_value: Path, *, base_dir: Path) -> Path:
    """Validate a user-supplied path against path traversal.

    Args:
        path_value: Candidate path from user input.
        base_dir: Allowed root directory that the resolved path must stay under.

    Returns:
        Resolved absolute path when validation succeeds.

    Raises:
        ValueError: If path contains `..` traversal segments or resolves outside base.
    """
    raw_path = str(path_value)
    if ".." in path_value.parts:
        raise ValueError("Path traversal is not allowed.")

    absolute_candidate = Path(os.path.abspath(raw_path))
    absolute_base = Path(os.path.abspath(str(base_dir)))
    if os.path.commonpath([str(absolute_candidate), str(absolute_base)]) != str(absolute_base):
        raise ValueError("Path must stay within the allowed project directory.")
    return absolute_candidate
