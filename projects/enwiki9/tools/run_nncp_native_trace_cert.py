#!/usr/bin/env python3
"""Run or audit the fixed-system NNCP native CUDA trace certificate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

from materialize_nncp_native_trace_observer import materialize


EXPECTED_TARBALL = (
    "7b4be2a5871186b82cd5f1c6137a8f6fed0d0c6b2bb281793db1f0be65831119"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def capture(command: list[str]) -> str | None:
    try:
        return subprocess.run(
            command,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def environment_receipt(source_package: Path) -> dict[str, object]:
    gpu = capture(
        [
            "nvidia-smi",
            "--query-gpu=name,uuid,driver_version",
            "--format=csv,noheader",
        ]
    )
    cuda = capture(["nvcc", "--version"])
    status = "NVIDIA_READY" if gpu and cuda else "BLOCKED_NVIDIA"
    return {
        "cuda_compiler": cuda,
        "execution_status": status,
        "gpu": gpu,
        "libcuda_visible": capture(["ldconfig", "-p"]),
        "source_package": {
            "bytes": source_package.stat().st_size,
            "sha256": sha256(source_package),
        },
    }


def run(command: list[str], environment: dict[str, str]) -> None:
    subprocess.run(command, check=True, env=environment)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-package", required=True, type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--expected-raw", type=Path)
    parser.add_argument("--dictionary", type=Path)
    parser.add_argument("--symbol-map-receipt", type=Path)
    parser.add_argument("--max-symbols", type=int)
    parser.add_argument("--full-windows", default="")
    parser.add_argument("--checkpoints", default="")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--audit-only", action="store_true")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    if sha256(args.source_package) != EXPECTED_TARBALL:
        raise ValueError("source package hash is not the frozen NNCP object")
    environment = environment_receipt(args.source_package)
    environment_path = args.output_dir / "environment.json"
    environment_path.write_text(
        json.dumps(environment, indent=2, sort_keys=True) + "\n"
    )
    if args.audit_only or environment["execution_status"] != "NVIDIA_READY":
        print(json.dumps(environment, indent=2, sort_keys=True))
        return 2 if environment["execution_status"] != "NVIDIA_READY" else 0
    if args.input is None:
        raise ValueError("--input is required for execution")
    if args.expected_raw is None:
        raise ValueError("--expected-raw is required for execution")

    with tempfile.TemporaryDirectory(prefix="nncp-native-trace-") as temp:
        workspace = Path(temp)
        with tarfile.open(args.source_package, "r:xz") as archive:
            archive.extractall(workspace)
        roots = [path for path in workspace.iterdir() if path.is_dir()]
        if len(roots) != 1:
            raise ValueError("unexpected NNCP archive layout")
        root = roots[0]
        patch = args.output_dir / "nncp_native_trace.patch"
        materialize(root / "cp_utils.c", root / "cp_utils.c.traced", patch)
        (root / "cp_utils.c").write_bytes((root / "cp_utils.c.traced").read_bytes())
        run(["make", "-C", str(root), "-j2"], os.environ.copy())

        binary = root / "nncp"
        trace_off = args.output_dir / "trace_off.nncp"
        trace_on = args.output_dir / "trace_on.nncp"
        trace = args.output_dir / "native_trace.bin"
        decoded = args.output_dir / "decoded.raw"
        command = [str(binary), "--cuda", "--profile", "enwik9"]
        if args.dictionary:
            command.extend(["--dict", str(args.dictionary)])
        else:
            command.extend(["--preprocess", "16384,512"])
        if args.max_symbols is not None:
            command.extend(["--max_size", str(args.max_symbols)])
        command.extend(["c", str(args.input)])

        native_environment = os.environ.copy()
        native_environment["LD_LIBRARY_PATH"] = str(root)
        off_environment = native_environment.copy()
        off_environment.pop("NNCP_NATIVE_TRACE", None)
        run([*command, str(trace_off)], off_environment)
        on_environment = native_environment.copy()
        on_environment["NNCP_NATIVE_TRACE"] = str(trace)
        on_environment["NNCP_NATIVE_TRACE_FULL_WINDOWS"] = args.full_windows
        on_environment["NNCP_NATIVE_TRACE_CHECKPOINTS"] = args.checkpoints
        run([*command, str(trace_on)], on_environment)
        run([str(binary), "--cuda", "d", str(trace_on), str(decoded)],
            off_environment)

        frozen = {
            **environment,
            "binary": {"bytes": binary.stat().st_size, "sha256": sha256(binary)},
            "command": command,
            "dictionary": (
                {"bytes": args.dictionary.stat().st_size,
                 "sha256": sha256(args.dictionary)}
                if args.dictionary
                else None
            ),
            "input": {"bytes": args.input.stat().st_size,
                      "sha256": sha256(args.input)},
            "libnc": {"sha256": sha256(root / "libnc.so")},
            "libnc_cuda": {"sha256": sha256(root / "libnc_cuda.so")},
            "patch": {"bytes": patch.stat().st_size, "sha256": sha256(patch)},
        }
        environment_path.write_text(
            json.dumps(frozen, indent=2, sort_keys=True) + "\n"
        )
        verifier = Path(__file__).with_name("verify_nncp_native_trace.py")
        verify_command = [
            "python3",
            str(verifier),
            "--trace",
            str(trace),
            "--trace-on-archive",
            str(trace_on),
            "--trace-off-archive",
            str(trace_off),
            "--decoded",
            str(decoded),
            "--expected-raw",
            str(args.expected_raw),
            "--environment",
            str(environment_path),
            "--receipt",
            str(args.output_dir / "decision.json"),
        ]
        if args.symbol_map_receipt:
            verify_command.extend(
                ["--symbol-map-receipt", str(args.symbol_map_receipt)]
            )
        run(verify_command, os.environ.copy())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
