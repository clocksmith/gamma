"""Identity-bound asset access with bounded source buffers and streaming copies."""
from pathlib import Path
import shutil
from .artifacts import fingerprint


class ArtifactResolver:
    def __init__(self, root: Path, records: tuple[dict, ...], *, buffer_limit=1024 * 1024):
        self.root = root
        self.records = {r["path"]: dict(r) for r in records}
        if len(self.records) != len(records):
            raise ValueError("duplicate artifact paths")
        self.buffer_limit = buffer_limit

    def verify(self, name: str) -> Path:
        ref = self.records[name]
        path = self.root / name
        actual = fingerprint(path, self.root)
        if actual["sha256"] != ref["sha256"].removeprefix("sha256:") or actual["bytes"] != ref["bytes"]:
            raise ValueError(f"bound artifact differs: {name}")
        return path

    def read_source(self, name: str) -> bytes:
        path = self.verify(name)
        if self.records[name]["bytes"] > self.buffer_limit:
            raise ValueError("artifact exceeds source buffer limit; use streaming copy")
        with path.open("rb") as stream:
            raw = stream.read(self.buffer_limit + 1)
        import hashlib
        if len(raw) > self.buffer_limit or hashlib.sha256(raw).hexdigest() != self.records[name]["sha256"].removeprefix("sha256:"):
            raise ValueError("source changed while buffered")
        return raw

    def copy(self, name: str, destination: Path) -> None:
        source = self.verify(name)
        with source.open("rb") as src, destination.open("xb") as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
        actual = fingerprint(destination, destination.parent)
        self.verify(name)
        if actual["sha256"] != self.records[name]["sha256"].removeprefix("sha256:"):
            raise ValueError("streaming copy differs")
