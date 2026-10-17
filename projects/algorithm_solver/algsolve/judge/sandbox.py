"""Run untrusted Python inside bubblewrap with explicit, tested limits.

The sandbox exposes only /usr (interpreter and stdlib), a read-only task
directory, a private /tmp, /proc and a minimal /dev. All namespaces are
unshared, so the program has no network and cannot see host processes.
Resource limits are applied with prlimit inside the namespace; the host
enforces wall time and output size and kills the whole process group.

Nothing here decides pass/fail. Callers compare outputs on the host.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

BWRAP = "/usr/bin/bwrap"
PRLIMIT = "/usr/bin/prlimit"
PYTHON = "/usr/bin/python3"


@dataclass(frozen=True)
class Limits:
    cpu_seconds: int = 2
    wall_seconds: float = 10.0
    memory_bytes: int = 512 * 1024 * 1024
    max_processes: int = 16
    max_file_bytes: int = 1024 * 1024
    max_open_files: int = 64
    max_output_bytes: int = 1024 * 1024


@dataclass
class SandboxResult:
    exit_code: int | None
    signal: int | None
    stdout: bytes
    stderr: bytes
    wall_seconds: float
    timed_out: bool = False
    output_limit_exceeded: bool = False
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return (
            self.exit_code == 0
            and not self.timed_out
            and not self.output_limit_exceeded
        )


class SandboxUnavailable(RuntimeError):
    """bwrap or prlimit missing; callers must fail closed."""


def check_available() -> None:
    for tool in (BWRAP, PRLIMIT, PYTHON):
        if not Path(tool).exists():
            raise SandboxUnavailable(f"required sandbox tool missing: {tool}")


def bwrap_argv(task_dir: Path, limits: Limits, argv: list[str]) -> list[str]:
    return [
        BWRAP,
        "--unshare-all",
        "--die-with-parent",
        "--new-session",
        "--clearenv",
        "--setenv", "PATH", "/usr/bin",
        "--setenv", "PYTHONHASHSEED", "0",
        "--setenv", "PYTHONDONTWRITEBYTECODE", "1",
        "--setenv", "HOME", "/tmp",
        "--setenv", "LANG", "C.UTF-8",
        "--hostname", "sandbox",
        "--ro-bind", "/usr", "/usr",
        "--symlink", "usr/lib", "/lib",
        "--symlink", "usr/lib64", "/lib64",
        "--symlink", "usr/bin", "/bin",
        "--proc", "/proc",
        "--dev", "/dev",
        "--tmpfs", "/tmp",
        "--ro-bind", str(task_dir), "/task",
        "--chdir", "/task",
        PRLIMIT,
        f"--cpu={limits.cpu_seconds}",
        f"--as={limits.memory_bytes}",
        f"--nproc={limits.max_processes}",
        f"--fsize={limits.max_file_bytes}",
        f"--nofile={limits.max_open_files}",
        "--core=0",
        "--",
        *argv,
    ]


def _kill_group(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def run(
    argv: list[str],
    *,
    files: dict[str, bytes | str],
    stdin: bytes = b"",
    limits: Limits = Limits(),
) -> SandboxResult:
    """Write `files` into a fresh task dir, run argv inside the sandbox."""
    check_available()
    task_dir = Path(tempfile.mkdtemp(prefix="algsolve-task-"))
    try:
        for name, content in files.items():
            if "/" in name or name.startswith("."):
                raise ValueError(f"task file names must be flat: {name!r}")
            data = content.encode("utf-8") if isinstance(content, str) else content
            (task_dir / name).write_bytes(data)
        task_dir.chmod(0o555)
        return _run_in(task_dir, argv, stdin, limits)
    finally:
        task_dir.chmod(0o755)
        shutil.rmtree(task_dir, ignore_errors=True)


def _run_in(task_dir: Path, argv: list[str], stdin: bytes, limits: Limits) -> SandboxResult:
    started = time.monotonic()
    proc = subprocess.Popen(
        bwrap_argv(task_dir, limits, argv),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
        env={"PATH": "/usr/bin"},
    )
    captured = {"stdout": bytearray(), "stderr": bytearray()}
    exceeded = threading.Event()

    def pump(stream, key: str) -> None:
        buf = captured[key]
        while True:
            chunk = stream.read(65536)
            if not chunk:
                return
            room = limits.max_output_bytes - len(buf)
            if len(chunk) > room:
                buf.extend(chunk[: max(room, 0)])
                exceeded.set()
                _kill_group(proc)
                return
            buf.extend(chunk)

    readers = [
        threading.Thread(target=pump, args=(proc.stdout, "stdout"), daemon=True),
        threading.Thread(target=pump, args=(proc.stderr, "stderr"), daemon=True),
    ]
    for reader in readers:
        reader.start()

    def feed() -> None:
        try:
            if stdin:
                proc.stdin.write(stdin)
            proc.stdin.close()
        except (BrokenPipeError, OSError):
            pass

    writer = threading.Thread(target=feed, daemon=True)
    writer.start()

    timed_out = False
    try:
        proc.wait(timeout=limits.wall_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_group(proc)
        proc.wait()
    # The pid namespace dies with bwrap; make sure any stragglers in the
    # session are gone before the readers are joined.
    _kill_group(proc)
    for reader in readers:
        reader.join(timeout=5)
    writer.join(timeout=1)
    wall = time.monotonic() - started

    code = proc.returncode
    sig = -code if code is not None and code < 0 else None
    # bwrap reports a child killed by signal N as exit status 128 + N.
    if sig is None and code is not None and code > 128:
        sig = code - 128
    return SandboxResult(
        exit_code=code,
        signal=sig,
        stdout=bytes(captured["stdout"]),
        stderr=bytes(captured["stderr"]),
        wall_seconds=wall,
        timed_out=timed_out,
        output_limit_exceeded=exceeded.is_set(),
    )


def run_python(
    source_name: str,
    *,
    files: dict[str, bytes | str],
    stdin: bytes = b"",
    limits: Limits = Limits(),
) -> SandboxResult:
    return run([PYTHON, "-I", "-S", source_name], files=files, stdin=stdin, limits=limits)
