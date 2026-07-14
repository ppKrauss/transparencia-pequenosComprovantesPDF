from __future__ import annotations

import hashlib
from pathlib import Path


def file_digest(path: str | Path, algorithm: str = "sha1", chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.new(algorithm)
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()
