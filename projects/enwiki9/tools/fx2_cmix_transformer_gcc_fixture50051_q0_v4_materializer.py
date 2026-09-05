"""Copy the fixed public source closure and verify every copied byte."""
import hashlib
from pathlib import Path
import shutil


def materialize(source: Path, work: Path, rows: list[dict]) -> None:
    work.mkdir(mode=0o700)
    for row in rows:
        destination = work / row["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        with (source / row["path"]).open("rb") as src, destination.open("xb") as dst:
            shutil.copyfileobj(src, dst)
        with destination.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        if destination.stat().st_size != row["bytes"] or digest != row["sha256"]:
            raise RuntimeError("copied public source identity drift: " + row["path"])
