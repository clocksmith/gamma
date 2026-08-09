#!/usr/bin/env python3
"""Certify the CPU-only XZ package for the exact NNCP midpoint codec."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import lzma
import math
from pathlib import Path
import subprocess
import tarfile
import tempfile


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_midsegment32_cpu_xz_package_qm0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
DONOR_TAR = Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05.tar.gz")
SOURCE_TAR = PROGRAM / "nncp_cpu_source.tar.xz"
PATCH_XZ = PROGRAM / "nncp_midsegment32.patch.xz"
PARENT_PATCH = (
    ROOT
    / "programs/nncp_libnc_exact_midsegment32_65536_qm3_v1/"
    "nncp_midsegment32.patch"
)
PARENT_DECISION = (
    ROOT / "results/nncp_libnc_exact_midsegment32_65536_qm3_v1/decision.json"
)
PARENT_AUDIT = (
    ROOT / "results/nncp_libnc_exact_midsegment32_65536_qm3_v1/strict_audit.json"
)
EXPECTED = {
    "donor_tar": "7b4be2a5871186b82cd5f1c6137a8f6fed0d0c6b2bb281793db1f0be65831119",
    "source_tar": "9b015bdbe9d2d625efd080021864717d39277502158472e825bacb05e2a70082",
    "patch_xz": "9d14e7614f62fa7c539ef1fe0c2ea4a26e9d0c0da1f70955a67de9129e8bd8fb",
    "parent_patch": "75512b77a0ececd35c63baca0614ca7f0999ab69a8b8a38d1063279d999f9766",
    "parent_binary": "cbe7108accae62a41ab885c4a14636b122adc43ec9b6ee59263c341731fe2fe0",
    "parent_archive": "c879411c5bfe4c8afb3998fd46fe367963da33fcd96130af559ddb7577991ce7",
}
REQUIRED_FILES = {
    "Makefile",
    "VERSION",
    "arith.c",
    "arith.h",
    "cmdopt.c",
    "cmdopt.h",
    "cp_utils.c",
    "cp_utils.h",
    "cutils.c",
    "cutils.h",
    "libnc.h",
    "libnc.so",
    "list.h",
    "nncp.c",
    "preprocess.c",
    "preprocess.h",
}
OMITTED_FILES = {"Changelog", "libnc_cuda.so", "readme.txt"}
MAX_PACKAGE_BYTES = 260_000
PARENT_PACKAGE_BYTES = 1_184_561
PUBLISHED_ARCHIVE_BYTES = 106_632_363
PUBLISHED_PACKAGE_BYTES = 628_955
TARGET_BYTES = 105_000_000
RESERVE_BYTES = 500_000
FULL_SYMBOLS = 200_608_961
MATURE_SYMBOLS = 1_998_848


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def run(command: list[str], cwd: Path) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
    }


def main() -> int:
    bound = {
        "donor_tar": DONOR_TAR,
        "source_tar": SOURCE_TAR,
        "patch_xz": PATCH_XZ,
        "parent_patch": PARENT_PATCH,
    }
    for name, path in bound.items():
        if not path.is_file() or sha256(path) != EXPECTED[name]:
            raise ValueError(f"{name} identity mismatch")
    parent = json.loads(PARENT_DECISION.read_text())
    audit = json.loads(PARENT_AUDIT.read_text())
    if parent["status"] != "AUTHORIZED_NATIVE_LARGER_GATE":
        raise ValueError("parent decision is not authorized")
    if audit["status"] != "PASS":
        raise ValueError("parent strict audit did not pass")
    if parent["program_accounting"]["compiled_candidate_binary"]["sha256"] != EXPECTED[
        "parent_binary"
    ]:
        raise ValueError("parent binary receipt mismatch")
    if parent["comparison"]["candidate_archive_sha256"] != EXPECTED["parent_archive"]:
        raise ValueError("parent archive receipt mismatch")

    program_files = sorted(path for path in PROGRAM.iterdir() if path.is_file())
    package_bytes = sum(path.stat().st_size for path in program_files)
    output_dir = ROOT / "results" / CANDIDATE_ID
    if output_dir.exists():
        raise SystemExit(f"refusing to replace existing output directory: {output_dir}")
    output_dir.mkdir(parents=True)

    with tempfile.TemporaryDirectory(prefix="nncp-midpoint-package-") as temp:
        temp_root = Path(temp)
        donor_root = temp_root / "donor"
        candidate_root = temp_root / "candidate"
        donor_root.mkdir()
        candidate_root.mkdir()
        with tarfile.open(DONOR_TAR, "r:gz") as archive:
            archive.extractall(donor_root)
        with tarfile.open(SOURCE_TAR, "r:xz") as archive:
            archive.extractall(candidate_root)
        donor_source = donor_root / "nncp-2024-06-05"
        donor_names = {path.name for path in donor_source.iterdir() if path.is_file()}
        candidate_names = {
            path.name for path in candidate_root.iterdir() if path.is_file()
        }
        if donor_names != REQUIRED_FILES | OMITTED_FILES:
            raise ValueError("unexpected donor top-level file set")
        if candidate_names != REQUIRED_FILES:
            raise ValueError("unexpected CPU-only source file set")
        source_identity = {
            name: sha256(donor_source / name) == sha256(candidate_root / name)
            for name in sorted(REQUIRED_FILES)
        }
        if not all(source_identity.values()):
            raise ValueError("CPU source subset differs from donor")

        decoded_patch = temp_root / "midpoint.patch"
        decoded_patch.write_bytes(lzma.decompress(PATCH_XZ.read_bytes()))
        if sha256(decoded_patch) != EXPECTED["parent_patch"]:
            raise ValueError("decoded midpoint patch differs from parent")
        patch_execution = run(
            ["patch", "-s", "-p1", "-i", str(decoded_patch)],
            candidate_root,
        )
        build_execution = run(["make", "-j4"], candidate_root)
        candidate_binary = candidate_root / "nncp"
        if sha256(candidate_binary) != EXPECTED["parent_binary"]:
            raise ValueError("rebuilt binary differs from exact q3 parent")

        spec = importlib.util.spec_from_file_location(
            "nncp_midpoint_package_program", PROGRAM / "program.py"
        )
        if spec is None or spec.loader is None:
            raise ValueError("cannot load package wrapper")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        wrapper_binary, _ = module._binary()
        wrapper_binary_identity = sha256(wrapper_binary) == EXPECTED["parent_binary"]
        if not wrapper_binary_identity:
            raise ValueError("wrapper rebuild differs from exact q3 parent")

    package_saving = PARENT_PACKAGE_BYTES - package_bytes
    package_delta_vs_published = package_bytes - PUBLISHED_PACKAGE_BYTES
    provisional_total = PUBLISHED_ARCHIVE_BYTES + package_bytes
    archive_debt = provisional_total - TARGET_BYTES
    archive_gain_with_reserve = archive_debt + RESERVE_BYTES
    normalized_gate = math.ceil(
        archive_gain_with_reserve * MATURE_SYMBOLS / FULL_SYMBOLS
    )
    failed: list[str] = []
    if package_bytes > MAX_PACKAGE_BYTES:
        failed.append("package_above_260000")
    if package_saving < 900_000:
        failed.append("package_saving_below_900000")
    promotion = not failed
    decision = {
        "schema": "enwiki9_nncp_libnc_midsegment32_cpu_xz_package_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "PASS" if promotion else "REJECT",
        "verdict": (
            "authorize_exact_cpu_only_midpoint_package"
            if promotion
            else "retire_cpu_only_midpoint_package"
        ),
        "score_credit_bytes": 0,
        "claim_boundary": (
            "Exact package-only identity certificate. The CPU source subset, "
            "midpoint patch, rebuilt binary, and wrapper-built binary match "
            "the strict q3 parent. No new corpus archive or full-1G score is claimed."
        ),
        "package": {
            "files": [artifact(path) for path in program_files],
            "bytes": package_bytes,
            "maximum_bytes": MAX_PACKAGE_BYTES,
            "parent_q3_package_bytes": PARENT_PACKAGE_BYTES,
            "saving_vs_q3_bytes": package_saving,
            "published_nncp_package_bytes": PUBLISHED_PACKAGE_BYTES,
            "delta_vs_published_bytes": package_delta_vs_published,
        },
        "identity": {
            "required_cpu_files": sorted(REQUIRED_FILES),
            "omitted_non_cpu_files": sorted(OMITTED_FILES),
            "all_required_files_byte_identical": all(source_identity.values()),
            "source_file_identity": source_identity,
            "decoded_patch_sha256": EXPECTED["parent_patch"],
            "rebuilt_binary_sha256": EXPECTED["parent_binary"],
            "wrapper_binary_identity": wrapper_binary_identity,
            "inherited_parent_archive_sha256": EXPECTED["parent_archive"],
        },
        "execution": {
            "patch": patch_execution,
            "build": build_execution,
        },
        "target_normalization": {
            "published_archive_bytes": PUBLISHED_ARCHIVE_BYTES,
            "candidate_package_bytes": package_bytes,
            "provisional_total_before_new_archive_gain": provisional_total,
            "target_bytes": TARGET_BYTES,
            "archive_debt_bytes": archive_debt,
            "reserve_bytes": RESERVE_BYTES,
            "required_full_symbol_archive_gain_with_reserve": archive_gain_with_reserve,
            "full_symbols": FULL_SYMBOLS,
            "mature_symbols": MATURE_SYMBOLS,
            "normalized_mature_gain_gate_bytes": normalized_gate,
        },
        "inputs": {
            **{name: artifact(path) for name, path in bound.items()},
            "parent_decision": artifact(PARENT_DECISION),
            "parent_audit": artifact(PARENT_AUDIT),
            "driver": artifact(Path(__file__).resolve()),
        },
        "failed_conditions": failed,
        "decision": {
            "promotion_authorized": promotion,
            "verified_full_1g_score_bytes": None,
            "target_bytes": TARGET_BYTES,
        },
    }
    (output_dir / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
