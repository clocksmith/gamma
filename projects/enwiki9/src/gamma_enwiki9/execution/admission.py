"""One concurrency domain for managed leases and queue admission."""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path


class AdmissionBusy(ValueError):
    pass


@contextmanager
def admission_guard(runtime: Path):
    runtime.mkdir(parents=True, exist_ok=True)
    fd = os.open(runtime, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise AdmissionBusy("exclusive lease publication or execution owns admission") from exc
        yield
    finally:
        os.close(fd)


def require_qualification_reservation(running: Path, job_id: str) -> None:
    rows = [json.loads(p.read_bytes()) for p in running.glob("*.json")]
    if len(rows) != 1 or rows[0].get("job_id") != job_id or rows[0].get("execution_mode") != "qualification":
        raise ValueError("qualification requires the sole queue reservation")
