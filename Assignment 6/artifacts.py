"""
artifacts.py — Content-addressable artifact store.

Large tool results (>4KB) are stored here as raw bytes. Memory holds only the
handle string ("art:<sha256[:16]>"). Decision sees artifact bytes only when
Perception explicitly attaches them for the current goal.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from schemas import Artifact

_BASE = Path(__file__).parent / "state" / "artifacts"


class ArtifactStore:
    def __init__(self, base_dir: Path = _BASE) -> None:
        self._dir = base_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def _sha(self, blob: bytes) -> str:
        return hashlib.sha256(blob).hexdigest()[:16]

    def put(self, blob: bytes, *, content_type: str, source: str, descriptor: str) -> str:
        sha = self._sha(blob)
        art_id = f"art:{sha}"
        bin_path = self._dir / f"{sha}.bin"
        meta_path = self._dir / f"{sha}.json"
        if not bin_path.exists():
            bin_path.write_bytes(blob)
            meta = Artifact(
                id=art_id,
                content_type=content_type,
                size_bytes=len(blob),
                source=source,
                descriptor=descriptor,
            )
            meta_path.write_text(meta.model_dump_json(indent=2), encoding="utf-8")
        return art_id

    def get_bytes(self, artifact_id: str) -> bytes:
        sha = artifact_id.removeprefix("art:")
        return (self._dir / f"{sha}.bin").read_bytes()

    def get_meta(self, artifact_id: str) -> Artifact:
        sha = artifact_id.removeprefix("art:")
        return Artifact.model_validate_json(
            (self._dir / f"{sha}.json").read_text(encoding="utf-8")
        )

    def exists(self, artifact_id: str) -> bool:
        if not artifact_id or not artifact_id.startswith("art:"):
            return False
        sha = artifact_id.removeprefix("art:")
        return (self._dir / f"{sha}.bin").exists()


# Module-level singleton used by action.py and agent6.py
artifacts = ArtifactStore()
