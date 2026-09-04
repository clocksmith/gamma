#!/usr/bin/env python3
"""Exact opening-1M CMIX stage with a clean env and exact decode filename."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
BASE_PATH = PROJECT / "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v14_telemetry.py"
SCHEMA = "gamma.enwiki9.cmix-obias-source-ppm-rss-env8192-opening1m-stage.v14"
POPULATION_BYTES = 1_000_000
POPULATION_SHA256 = "369b688978f649681136198fb96db14c1616756260c55fb4b65e9bc049552cad"
PACKAGE_BYTES = 468_481
PACKAGE_SHA256 = "4ba53d3652c4e6de4126b4c03006e45a5f7e0511abd5d9661bf8132236ef1d2a"
HEAD_BYTES = 23_002
HEAD_SHA256 = "35cd24fed87c3409994abf5573b5697be19ea03b5ece0928b69b1cdc4f3b6078"
ARCHIVE_BYTES = 464_298
ARCHIVE_SHA256 = "9065eaf54f81e441598fd53c39f909db49d6a9627ae0456eabb8c77099b8ccc4"


def load_base() -> Any:
    if BASE_PATH.is_symlink() or BASE_PATH.resolve(strict=True) != BASE_PATH.absolute() or BASE_PATH.stat().st_size != 19008 or hashlib.sha256(BASE_PATH.read_bytes()).hexdigest() != "aec29c8522f3437d3d911d34fc8b00e88302ff6523080ed464657dd8026bbd69":
        raise RuntimeError("v14 telemetry dependency drift before import")
    spec = importlib.util.spec_from_file_location("cmix_q0_v3_stage_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen stage base")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
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
    phase = f"opening1m_{args.arm.lower().replace('-', '_')}"
    base.append_phase(phase, "start")

    if args.mode == "encode":
        if args.input is None or args.package is None or args.head is None or args.archive is not None:
            raise RuntimeError("encode artifact arguments are incomplete")
        input_path = base.verify(args.input, POPULATION_BYTES, POPULATION_SHA256, "population")
        package_path = base.verify(args.package, PACKAGE_BYTES, PACKAGE_SHA256, "package")
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
        payload = base.verify(payload_path, 172_605, "a723ca62ae2237354888dc23c3e2bb08eb166276719a011eb95bf52774d70db7", "fresh payload")
        archive = base.verify(archive_path, ARCHIVE_BYTES, ARCHIVE_SHA256, "fresh archive")
        base.copy_new(payload, result_root / "out.cmix")
        base.copy_new(archive, result_root / "archive9", 0o700)
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
        if args.archive is None or any(value is not None for value in (args.input, args.package, args.head)):
            raise RuntimeError("decode artifact arguments are incomplete")
        archive_path = base.verify(args.archive, ARCHIVE_BYTES, ARCHIVE_SHA256, "archive")
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
        restored = base.verify(restored, POPULATION_BYTES, POPULATION_SHA256, "restored population")
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
