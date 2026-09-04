#!/usr/bin/env python3
"""Exact opening-100M CMIX stage with zombie-safe process telemetry."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
BASE_PATH = PROJECT / "tools/cmix_obias_source_ppm_rss_env8192_zombiefix_q0_v1_telemetry.py"
BASE_BYTES = 21_725
BASE_SHA256 = "e89dbb909526a4f7e9752c233df1f4e8afdd49dc86fd168d0da25796c8d1b939"
SCHEMA = "gamma.enwiki9.cmix-obias-source-ppm-rss-env8192-opening100m-stage.resource-q0-v1"
POPULATION_BYTES = 100_000_000
POPULATION_SHA256 = "2b49720ec4d78c3c9fabaee6e4179a5e997302b3a70029f30f2d582218c024a8"
PACKAGE_BYTES = 468_481
PACKAGE_SHA256 = "4ba53d3652c4e6de4126b4c03006e45a5f7e0511abd5d9661bf8132236ef1d2a"
HEAD_BYTES = 23_002
HEAD_SHA256 = "35cd24fed87c3409994abf5573b5697be19ea03b5ece0928b69b1cdc4f3b6078"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_base() -> Any:
    if (
        BASE_PATH.is_symlink()
        or BASE_PATH.resolve(strict=True) != BASE_PATH.absolute()
        or BASE_PATH.stat().st_size != BASE_BYTES
        or sha256_file(BASE_PATH) != BASE_SHA256
    ):
        raise RuntimeError("zombie-safe telemetry dependency drift before import")
    specification = importlib.util.spec_from_file_location(
        "cmix_opening100m_zombie_safe_telemetry", BASE_PATH
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("cannot load zombie-safe telemetry")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def require_absent(path: Path, label: str) -> None:
    if path.exists() or path.is_symlink():
        raise RuntimeError(f"{label} must be absent: {path}")


def clean_environment(head: Path | None, ppm: str) -> dict[str, str]:
    value = {
        "PATH": "/usr/bin:/bin",
        "GAMMA_RESOURCE_PHASE_MARKERS": os.environ["GAMMA_RESOURCE_PHASE_MARKERS"],
    }
    if head is not None:
        value["KH_BITLSTM32"] = str(head)
    if ppm == "8192":
        value["CMIX_PPM_RSS_MB"] = "8192"
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("encode", "decode"), required=True)
    parser.add_argument("--arm", choices=("P", "E-A", "E-B", "E-decode"), required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--package", type=Path)
    parser.add_argument("--head", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--archive-bytes", type=int)
    parser.add_argument("--archive-sha256")
    parser.add_argument("--ppm-rss-mb", choices=("default", "8192"), required=True)
    args = parser.parse_args()

    expected_arm_mode = {
        "P": ("encode", "default"),
        "E-A": ("encode", "8192"),
        "E-B": ("encode", "8192"),
        "E-decode": ("decode", "8192"),
    }
    if (args.mode, args.ppm_rss_mb) != expected_arm_mode[args.arm]:
        raise RuntimeError("arm, mode, and environment treatment do not match")
    base = load_base()
    work_root = args.work_root.resolve()
    result_root = args.result_root.resolve(strict=True)
    receipt = args.receipt.resolve()
    require_absent(work_root, "stage work root")
    if receipt.parent != result_root:
        raise RuntimeError("stage receipt must be a direct result-root child")
    require_absent(receipt, "stage receipt")
    if result_root == work_root or result_root in work_root.parents or work_root in result_root.parents:
        raise RuntimeError("stage work and result roots must be disjoint")
    work_root.mkdir(mode=0o700)
    phase = f"opening100m_{args.arm.lower().replace('-', '_')}"
    base.append_phase(phase, "start")

    if args.mode == "encode":
        if (
            args.input is None
            or args.package is None
            or args.head is None
            or args.archive is not None
            or args.archive_bytes is not None
            or args.archive_sha256 is not None
        ):
            raise RuntimeError("encode artifact arguments are incomplete")
        input_path = base.verify(
            args.input, POPULATION_BYTES, POPULATION_SHA256, "population"
        )
        package_path = base.verify(
            args.package, PACKAGE_BYTES, PACKAGE_SHA256, "package"
        )
        head_path = base.verify(args.head, HEAD_BYTES, HEAD_SHA256, "head")
        local_package = work_root / "cmix"
        local_head = work_root / "head.blob"
        base.copy_new(package_path, local_package, 0o700)
        base.copy_new(head_path, local_head)
        command = [str(local_package), "-e", str(input_path), "out.cmix"]
        environment = clean_environment(local_head, args.ppm_rss_mb)
        execution = base.run_observed(
            command,
            work_root,
            environment,
            result_root / "codec.stdout",
            result_root / "codec.stderr",
        )
        base.write_json_new(result_root / "execution.json", execution)
        if execution["returncode"] != 0 or execution["measurement_complete"] is not True:
            raise RuntimeError("encode or process-tree telemetry failed")
        payload_path = work_root / "out.cmix"
        archive_path = work_root / "archive9"
        payload = base.artifact(payload_path)
        archive = base.artifact(archive_path)
        if payload["bytes"] <= 0 or archive["bytes"] <= 0:
            raise RuntimeError("encode produced an empty output")
        base.copy_new(payload_path, result_root / "out.cmix")
        base.copy_new(archive_path, result_root / "archive9", 0o700)
        inputs = {
            "population": base.artifact(input_path),
            "package": base.artifact(package_path),
            "head": base.artifact(head_path),
        }
        outputs = {
            "payload": base.artifact(result_root / "out.cmix"),
            "archive": base.artifact(result_root / "archive9"),
        }
    else:
        if (
            args.archive is None
            or args.archive_bytes is None
            or args.archive_sha256 is None
            or any(value is not None for value in (args.input, args.package, args.head))
        ):
            raise RuntimeError("decode artifact arguments are incomplete")
        if args.archive_bytes <= 0 or len(args.archive_sha256) != 64:
            raise RuntimeError("decode archive binding is malformed")
        archive_path = base.verify(
            args.archive, args.archive_bytes, args.archive_sha256, "treatment archive"
        )
        local_archive = work_root / "archive9"
        base.copy_new(archive_path, local_archive, 0o700)
        command = [str(local_archive)]
        environment = clean_environment(None, args.ppm_rss_mb)
        execution = base.run_observed(
            command,
            work_root,
            environment,
            result_root / "codec.stdout",
            result_root / "codec.stderr",
        )
        base.write_json_new(result_root / "execution.json", execution)
        if execution["returncode"] != 0 or execution["measurement_complete"] is not True:
            raise RuntimeError("decode or process-tree telemetry failed")
        restored = work_root / "enwik9_uncompressed"
        forbidden = work_root / "enwik9"
        if forbidden.exists() or forbidden.is_symlink():
            raise RuntimeError("decode created forbidden ambiguous filename enwik9")
        restored = base.verify(
            restored, POPULATION_BYTES, POPULATION_SHA256, "restored population"
        )
        base.copy_new(restored, result_root / "enwik9_uncompressed")
        inputs = {"archive": base.artifact(archive_path)}
        outputs = {"restored": base.artifact(result_root / "enwik9_uncompressed")}

    base.append_phase(phase, "end")
    value = {
        "schema": SCHEMA,
        "scope_bytes": POPULATION_BYTES,
        "arm": args.arm,
        "mode": args.mode,
        "ppm_rss_environment": (
            {} if args.ppm_rss_mb == "default" else {"CMIX_PPM_RSS_MB": "8192"}
        ),
        "clean_codec_environment": environment,
        "inputs": inputs,
        "outputs": outputs,
        "execution": execution,
        "execution_artifact": base.artifact(result_root / "execution.json"),
        "exact_decode_filename": "enwik9_uncompressed" if args.mode == "decode" else None,
        "phase_marker_path": os.environ["GAMMA_RESOURCE_PHASE_MARKERS"],
        "stage_pass": True,
    }
    base.write_json_new(receipt, value)
    print(json.dumps(value, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
