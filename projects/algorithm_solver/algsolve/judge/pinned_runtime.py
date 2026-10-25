"""Versioned, hash-pinned Node runtime adapter; historical sandbox stays unchanged.

The only namespace addition is a trusted executable read-only at /runtime/node.
No loader trick, environment inheritance, broader mount or host source execution.
Monitor implementation is preserved from sandbox.py (independent copy to avoid
process-global monkeypatches); its hash is bound by every runtime manifest.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from . import sandbox
from .sandbox import Limits, SandboxResult, SandboxUnavailable

SCHEMA = "gamma.pinned-node-runtime.v1"
NODE_SHA256 = "61ab14cd750fc24d5db53490ec5fc40f756e4b6e136b78cf7004265471d9bd1d"
NODE_BYTES = 126939688
RUNTIME_PATH = "/runtime/node"
# Exact dependency closure for the approved x86_64 binary, plus execution tools.
# Symlink destinations are pinned too; a different host needs a new manifest.
DEPENDENCIES = (
    "/usr/lib/x86_64-linux-gnu/libdl.so.2",
    "/usr/lib/x86_64-linux-gnu/libstdc++.so.6",
    "/usr/lib/x86_64-linux-gnu/libm.so.6",
    "/usr/lib/x86_64-linux-gnu/libgcc_s.so.1",
    "/usr/lib/x86_64-linux-gnu/libpthread.so.0",
    "/usr/lib/x86_64-linux-gnu/libc.so.6",
    "/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2",
    "/usr/bin/python3", "/usr/bin/bwrap", "/usr/bin/prlimit",
)


def _hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def freeze_runtime(node_path: Path) -> dict:
    """Inspect trusted runtime only; never execute a candidate or interpreter."""
    node_path = Path(node_path)
    if not node_path.is_file() or not os.access(node_path, os.X_OK):
        raise SandboxUnavailable("pinned Node must already be an executable regular file")
    if _hash(node_path) != NODE_SHA256:
        raise SandboxUnavailable("Node bytes do not match approved runtime identity")
    if node_path.stat().st_size != NODE_BYTES:
        raise SandboxUnavailable("approved Node size mismatch")
    return _current_manifest()


def _current_manifest() -> dict:
    return {
        "schema": SCHEMA, "node_sha256": NODE_SHA256,
        "node_bytes": NODE_BYTES, "sandbox_path": RUNTIME_PATH,
        "dependencies": [{"path": name, "resolved": str(Path(name).resolve(strict=True)),
                          "sha256": _hash(Path(name))} for name in DEPENDENCIES],
        "sandbox_sha256": _hash(Path(sandbox.__file__)),
        "adapter_sha256": _hash(Path(__file__)),
        "isolation": "existing-unshare-all-plus-one-readonly-executable",
    }


def validate_manifest(manifest: dict) -> None:
    """Verify complete frozen identity against this host without needing Node path."""
    if manifest != _current_manifest():
        raise SandboxUnavailable("runtime manifest identity or dependency drift")


def bwrap_argv(task_dir: Path, limits: Limits, argv: list[str], runtime: Path) -> list[str]:
    command = sandbox.bwrap_argv(task_dir, limits, argv)
    # Insert before the final prlimit command; never mount the containing host dir.
    at = command.index(sandbox.PRLIMIT)
    command[at:at] = ["--dir", "/runtime", "--ro-bind", str(runtime), RUNTIME_PATH]
    return command


def run_node(node_path: Path, *, manifest: dict, files: dict[str, bytes | str],
             stdin: bytes = b"", limits: Limits = Limits(),
             node_args: list[str] | None = None) -> SandboxResult:
    """Run Node directly in unchanged isolation plus the pinned read-only binary.

    The manifest must have been frozen before candidate execution. The source is
    copied into a private snapshot and checked again, so path replacement cannot
    change the bytes executed. The candidate cannot write that read-only mount.
    """
    sandbox.check_available()
    if freeze_runtime(Path(node_path)) != manifest:
        raise SandboxUnavailable("runtime manifest drift")
    if node_args is None:
        node_args = ["--jitless", "--single-threaded", "--max-old-space-size=64", "runner.cjs"]
    with tempfile.TemporaryDirectory(prefix="algsolve-pinned-runtime-") as directory:
        root = Path(directory)
        runtime = root / "node"
        with Path(node_path).open("rb") as source, runtime.open("xb") as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)
        if _hash(runtime) != NODE_SHA256 or runtime.stat().st_size != manifest["node_bytes"]:
            raise SandboxUnavailable("runtime changed while snapshotting")
        runtime.chmod(0o555)
        task_dir = root / "task"
        task_dir.mkdir(mode=0o700)
        try:
            for name, content in files.items():
                if not name or "/" in name or name.startswith("."):
                    raise ValueError(f"task file names must be flat: {name!r}")
                (task_dir / name).write_bytes(content.encode("utf-8") if isinstance(content, str) else content)
            task_dir.chmod(0o555)
            with tempfile.TemporaryFile() as status:
                return _run_monitored(task_dir, [RUNTIME_PATH, *node_args], stdin, limits, status, runtime)
        finally:
            task_dir.chmod(0o700)

def _kill_group(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _payload_exited(status: bytes, exit_code: int | None) -> bool:
    if len(status) > 4096:
        return False
    try:
        records = [json.loads(line) for line in status.splitlines() if line.strip()]
    except (ValueError, UnicodeDecodeError):
        return False
    if any(not isinstance(record, dict) for record in records):
        return False
    exits = [record['exit-code'] for record in records if 'exit-code' in record]
    return len(exits) == 1 and type(exits[0]) is int and 0 <= exits[0] <= 255 and exits[0] == exit_code


def _wait_for_exit(proc: subprocess.Popen, timeout: float) -> int:
    """Wait for the same child exit without timed-wait polling latency on Linux.

    The descriptor is host-only and observes the bubblewrap monitor. Unsupported
    kernels retain Popen.wait; namespace, status verification and cleanup stay
    with the caller. Always reap the child after its exit notification.
    """
    deadline = time.monotonic() + timeout
    try:
        descriptor = os.pidfd_open(proc.pid)
    except (AttributeError, OSError):
        return proc.wait(timeout=max(0., deadline - time.monotonic()))
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(descriptor, selectors.EVENT_READ)
            if not selector.select(max(0., deadline - time.monotonic())):
                raise subprocess.TimeoutExpired(proc.args, timeout)
        return proc.wait()
    finally:
        os.close(descriptor)


def _run_monitored(task_dir: Path, argv: list[str], stdin: bytes, limits: Limits, status, runtime: Path) -> SandboxResult:
    started = time.monotonic()
    command = bwrap_argv(task_dir, limits, argv, runtime)
    command[1:1] = ['--json-status-fd', str(status.fileno())]
    try:
        proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
            pass_fds=(status.fileno(),),
            env={"PATH": "/usr/bin"},
        )
    except OSError as error:
        raise SandboxUnavailable(f'Cannot start bubblewrap: {error}') from error
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
        try:
            _wait_for_exit(proc, limits.wall_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
    finally:
        # Cancellation must kill the namespace before releasing its task files.
        _kill_group(proc)
        proc.wait()
        for reader in readers:
            reader.join(timeout=5)
        writer.join(timeout=1)
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            stream.close()
    wall = time.monotonic() - started

    code = proc.returncode
    status.seek(0)
    if not timed_out and not exceeded.is_set() and not _payload_exited(status.read(4097), code):
        detail = bytes(captured['stderr'])[-600:].decode('utf-8', 'replace')
        raise SandboxUnavailable(f'Bubblewrap did not confirm payload execution (exit={code}): {detail}')
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

