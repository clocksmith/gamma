#!/usr/bin/env python3
"""Certify the midpoint CPU package with normalized-path build identity."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import lzma
import math
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

import nncp_libnc_midsegment32_cpu_xz_package_qm0 as q0


CANDIDATE_ID = "nncp_libnc_midsegment32_cpu_xz_package_qm1_v1"
PROGRAM = q0.ROOT / "programs" / CANDIDATE_ID
SOURCE_TAR = PROGRAM / "nncp_cpu_source.tar.xz"
PATCH_XZ = PROGRAM / "nncp_midsegment32.patch.xz"


def build_midpoint(source_root: Path, patch_path: Path) -> dict[str, object]:
    initial = q0.run(["make", "-j4"], source_root)
    patch = q0.run(["patch", "-s", "-p1", "-i", str(patch_path)], source_root)
    final = q0.run(["make", "-j4"], source_root)
    binary = source_root / "nncp"
    return {
        "initial_build": initial,
        "patch": patch,
        "final_build": final,
        "binary_bytes": binary.read_bytes(),
        "binary_sha256": q0.sha256(binary),
    }


def main() -> int:
    bound = {
        "donor_tar": q0.DONOR_TAR,
        "source_tar": SOURCE_TAR,
        "patch_xz": PATCH_XZ,
        "parent_patch": q0.PARENT_PATCH,
    }
    for name, path in bound.items():
        if not path.is_file() or q0.sha256(path) != q0.EXPECTED[name]:
            raise ValueError(f"{name} identity mismatch")
    parent = json.loads(q0.PARENT_DECISION.read_text())
    audit = json.loads(q0.PARENT_AUDIT.read_text())
    if parent["status"] != "AUTHORIZED_NATIVE_LARGER_GATE":
        raise ValueError("parent decision is not authorized")
    if audit["status"] != "PASS":
        raise ValueError("parent strict audit did not pass")
    if parent["comparison"]["candidate_archive_sha256"] != q0.EXPECTED[
        "parent_archive"
    ]:
        raise ValueError("parent archive receipt mismatch")

    program_files = sorted(path for path in PROGRAM.iterdir() if path.is_file())
    package_bytes = sum(path.stat().st_size for path in program_files)
    output_dir = q0.ROOT / "results" / CANDIDATE_ID
    if output_dir.exists():
        raise SystemExit(f"refusing to replace existing output directory: {output_dir}")
    output_dir.mkdir(parents=True)

    with tempfile.TemporaryDirectory(prefix="nncp-midpoint-package-qm1-") as temp:
        temp_root = Path(temp)
        donor_stage = temp_root / "donor_stage"
        candidate_stage = temp_root / "candidate_stage"
        build_root = temp_root / "normalized_build"
        donor_stage.mkdir()
        candidate_stage.mkdir()
        with tarfile.open(q0.DONOR_TAR, "r:gz") as archive:
            archive.extractall(donor_stage)
        with tarfile.open(SOURCE_TAR, "r:xz") as archive:
            archive.extractall(candidate_stage)
        donor_source = donor_stage / "nncp-2024-06-05"
        donor_names = {path.name for path in donor_source.iterdir() if path.is_file()}
        candidate_names = {
            path.name for path in candidate_stage.iterdir() if path.is_file()
        }
        if donor_names != q0.REQUIRED_FILES | q0.OMITTED_FILES:
            raise ValueError("unexpected donor top-level file set")
        if candidate_names != q0.REQUIRED_FILES:
            raise ValueError("unexpected CPU-only source file set")
        source_identity = {
            name: q0.sha256(donor_source / name)
            == q0.sha256(candidate_stage / name)
            for name in sorted(q0.REQUIRED_FILES)
        }
        if not all(source_identity.values()):
            raise ValueError("CPU source subset differs from donor")

        decoded_patch = temp_root / "midpoint.patch"
        decoded_patch.write_bytes(lzma.decompress(PATCH_XZ.read_bytes()))
        if q0.sha256(decoded_patch) != q0.EXPECTED["parent_patch"]:
            raise ValueError("decoded midpoint patch differs from parent")

        shutil.move(str(donor_source), str(build_root))
        donor_build = build_midpoint(build_root, decoded_patch)
        donor_binary = donor_build.pop("binary_bytes")
        shutil.rmtree(build_root)

        shutil.move(str(candidate_stage), str(build_root))
        candidate_build = build_midpoint(build_root, decoded_patch)
        candidate_binary = candidate_build.pop("binary_bytes")
        normalized_binary_identity = candidate_binary == donor_binary
        if not normalized_binary_identity:
            raise ValueError("normalized-path donor and subset ELFs differ")
        normalized_binary_sha256 = hashlib.sha256(candidate_binary).hexdigest()
        shutil.rmtree(build_root)

        prior_build_dir = os.environ.get("NNCP_BUILD_DIR")
        os.environ["NNCP_BUILD_DIR"] = str(build_root)
        try:
            spec = importlib.util.spec_from_file_location(
                "nncp_midpoint_package_qm1_program", PROGRAM / "program.py"
            )
            if spec is None or spec.loader is None:
                raise ValueError("cannot load package wrapper")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            wrapper_binary, _ = module._binary()
            wrapper_binary_identity = wrapper_binary.read_bytes() == donor_binary
        finally:
            if prior_build_dir is None:
                os.environ.pop("NNCP_BUILD_DIR", None)
            else:
                os.environ["NNCP_BUILD_DIR"] = prior_build_dir
        if not wrapper_binary_identity:
            raise ValueError("normalized-path wrapper ELF differs from donor")

    package_saving = q0.PARENT_PACKAGE_BYTES - package_bytes
    package_delta_vs_published = package_bytes - q0.PUBLISHED_PACKAGE_BYTES
    provisional_total = q0.PUBLISHED_ARCHIVE_BYTES + package_bytes
    archive_debt = provisional_total - q0.TARGET_BYTES
    archive_gain_with_reserve = archive_debt + q0.RESERVE_BYTES
    normalized_gate = math.ceil(
        archive_gain_with_reserve * q0.MATURE_SYMBOLS / q0.FULL_SYMBOLS
    )
    failed: list[str] = []
    if package_bytes > q0.MAX_PACKAGE_BYTES:
        failed.append("package_above_260000")
    if package_saving < 900_000:
        failed.append("package_saving_below_900000")
    promotion = not failed
    decision = {
        "schema": "enwiki9_nncp_libnc_midsegment32_cpu_xz_package_qm1_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "PASS" if promotion else "REJECT",
        "verdict": (
            "authorize_normalized_exact_cpu_only_midpoint_package"
            if promotion
            else "retire_normalized_cpu_only_midpoint_package"
        ),
        "score_credit_bytes": 0,
        "claim_boundary": (
            "Exact package-only certificate. Donor and CPU-only source builds "
            "are byte-identical at one normalized path after identical clean "
            "build, midpoint patch, and relink steps. The strict q3 archive and "
            "raw proof are inherited; no new full-corpus archive is claimed."
        ),
        "package": {
            "files": [q0.artifact(path) for path in program_files],
            "bytes": package_bytes,
            "maximum_bytes": q0.MAX_PACKAGE_BYTES,
            "parent_q3_package_bytes": q0.PARENT_PACKAGE_BYTES,
            "saving_vs_q3_bytes": package_saving,
            "published_nncp_package_bytes": q0.PUBLISHED_PACKAGE_BYTES,
            "delta_vs_published_bytes": package_delta_vs_published,
        },
        "identity": {
            "required_cpu_files": sorted(q0.REQUIRED_FILES),
            "omitted_non_cpu_files": sorted(q0.OMITTED_FILES),
            "all_required_files_byte_identical": all(source_identity.values()),
            "source_file_identity": source_identity,
            "decoded_patch_sha256": q0.EXPECTED["parent_patch"],
            "normalized_binary_identity": normalized_binary_identity,
            "normalized_binary_sha256": normalized_binary_sha256,
            "wrapper_binary_identity": wrapper_binary_identity,
            "path_specific_parent_binary_sha256": q0.EXPECTED["parent_binary"],
            "inherited_parent_archive_sha256": q0.EXPECTED["parent_archive"],
        },
        "execution": {
            "donor_build": donor_build,
            "candidate_build": candidate_build,
        },
        "target_normalization": {
            "published_archive_bytes": q0.PUBLISHED_ARCHIVE_BYTES,
            "candidate_package_bytes": package_bytes,
            "provisional_total_before_new_archive_gain": provisional_total,
            "target_bytes": q0.TARGET_BYTES,
            "archive_debt_bytes": archive_debt,
            "reserve_bytes": q0.RESERVE_BYTES,
            "required_full_symbol_archive_gain_with_reserve": archive_gain_with_reserve,
            "full_symbols": q0.FULL_SYMBOLS,
            "mature_symbols": q0.MATURE_SYMBOLS,
            "normalized_mature_gain_gate_bytes": normalized_gate,
        },
        "inputs": {
            **{name: q0.artifact(path) for name, path in bound.items()},
            "parent_decision": q0.artifact(q0.PARENT_DECISION),
            "parent_audit": q0.artifact(q0.PARENT_AUDIT),
            "driver": q0.artifact(Path(__file__).resolve()),
        },
        "failed_conditions": failed,
        "decision": {
            "promotion_authorized": promotion,
            "verified_full_1g_score_bytes": None,
            "target_bytes": q0.TARGET_BYTES,
        },
    }
    (output_dir / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
