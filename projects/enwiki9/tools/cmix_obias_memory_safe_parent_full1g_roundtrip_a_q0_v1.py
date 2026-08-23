#!/usr/bin/env python3
"""Dormant full-corpus Arm A for the probability-identical memory-safe parent."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import traceback

import cmix_obias_source_full1g_roundtrip_a_qm0 as baseline


ROOT = baseline.ROOT
CANDIDATE_ID = "cmix_obias_memory_safe_parent_full1g_roundtrip_a_q0_v1"
RESULT = ROOT / "projects/enwiki9/results" / CANDIDATE_ID
PROGRAM_DIR = (
    ROOT
    / "projects/enwiki9/programs/cmix_obias_memory_safe_parent_q0_v1"
)
PROGRAM_LOCK = PROGRAM_DIR / "program-lock.json"
REPEAT_REFERENCE: Path | None = None

PARENT_RESULT = (
    ROOT
    / "projects/enwiki9/results/cmix_obias_source_full1g_roundtrip_a_qm0_v1"
)
PARENT_PAYLOAD = PARENT_RESULT / "out.cmix"
PARENT_PAYLOAD_BYTES = 107_730_531
PARENT_PAYLOAD_SHA256 = (
    "889aa8074e0a84eb89997986899f1ef9f7cc0e52e87d1d36f86899fc679f5490"
)

LOCK_SCHEMA = "gamma.enwiki9.cmix_obias_memory_safe_parent.program_lock.v1"
LOCK_CANDIDATE = "cmix_obias_memory_safe_parent_q0_v1"
PHASE_MARKER: Path | None = None


def _inside_root(path: Path) -> bool:
    return path == ROOT or ROOT in path.parents


def _resolve_project_path(value: str, label: str) -> Path:
    relative = Path(value)
    if relative.is_absolute():
        raise RuntimeError(f"{label} must be project-relative")
    resolved = (ROOT / relative).resolve()
    if not _inside_root(resolved):
        raise RuntimeError(f"{label} escapes the workspace")
    return resolved


def _verify_locked_artifact(base: Path, record: object, label: str) -> Path:
    if not isinstance(record, dict):
        raise RuntimeError(f"program lock {label} is not an object")
    path_value = record.get("path")
    expected_bytes = record.get("bytes")
    expected_sha256 = record.get("sha256")
    if not isinstance(path_value, str) or not path_value:
        raise RuntimeError(f"program lock {label}.path is invalid")
    relative = Path(path_value)
    if relative.is_absolute():
        raise RuntimeError(f"program lock {label}.path must be relative")
    path = (base / relative).resolve()
    if not _inside_root(path):
        raise RuntimeError(f"program lock {label}.path escapes the workspace")
    if not path.is_file():
        raise RuntimeError(f"program lock {label} is missing: {path}")
    actual = baseline.artifact(path)
    if actual["bytes"] != expected_bytes or actual["sha256"] != expected_sha256:
        raise RuntimeError(f"program lock {label} identity mismatch")
    return path


def load_program_lock() -> tuple[dict, Path, Path]:
    if not PROGRAM_LOCK.is_file():
        raise RuntimeError(
            "dormant dependency: independently verified program-lock.json is absent"
        )
    lock = json.loads(PROGRAM_LOCK.read_text(encoding="utf-8"))
    if lock.get("schema") != LOCK_SCHEMA:
        raise RuntimeError("program lock schema mismatch")
    if lock.get("operational_status") != "frozen":
        raise RuntimeError("program lock is not frozen")
    if lock.get("candidate_id") != LOCK_CANDIDATE:
        raise RuntimeError("program lock candidate mismatch")
    if lock.get("independent_build_identity_pass") is not True:
        raise RuntimeError("independent build identity has not passed")

    program_reference = _resolve_project_path(
        lock.get("program_reference", ""), "program_reference"
    )
    if not program_reference.is_dir():
        raise RuntimeError("program_reference is not a directory")
    cmix = _verify_locked_artifact(program_reference, lock.get("cmix"), "cmix")
    head = _verify_locked_artifact(program_reference, lock.get("head"), "head")

    source = lock.get("source_binding")
    if not isinstance(source, dict):
        raise RuntimeError("source_binding is missing")
    for key, length in (("outer_commit", 40), ("tracked_tree", 40)):
        value = source.get(key)
        if not isinstance(value, str) or len(value) != length:
            raise RuntimeError(f"source_binding.{key} is invalid")
    patch_sha = source.get("patch_sha256")
    if not isinstance(patch_sha, str) or len(patch_sha) != 64:
        raise RuntimeError("source_binding.patch_sha256 is invalid")
    inputs = source.get("input_files")
    if not isinstance(inputs, list) or len(inputs) < 2:
        raise RuntimeError("source_binding.input_files is incomplete")
    for index, record in enumerate(inputs):
        _verify_locked_artifact(ROOT, record, f"source_binding.input_files[{index}]")
    _verify_locked_artifact(ROOT, lock.get("build_receipt"), "build_receipt")
    return lock, cmix, head


def initialize_phase_marker() -> Path:
    raw = os.environ.get("GAMMA_RESOURCE_PHASE_MARKERS")
    if not raw:
        raise RuntimeError("GAMMA_RESOURCE_PHASE_MARKERS is required")
    path = Path(raw).resolve()
    if not path.is_file():
        raise RuntimeError("phase marker file must exist before launch")
    if path.stat().st_size != 0:
        raise RuntimeError("phase marker file must be empty before launch")
    return path


def phase(phase_name: str, event: str, detail: str | None = None) -> None:
    if PHASE_MARKER is None:
        raise RuntimeError("phase marker is not initialized")
    record = {"event": event, "phase": phase_name}
    if detail is not None:
        record["detail"] = detail
    with PHASE_MARKER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
        handle.write("\n")


def _repeat_identity(reference: Path, payload: Path, archive: Path) -> dict:
    reference_payload = reference / "out.cmix"
    reference_archive = reference / "archive9"
    if not reference_payload.is_file() or not reference_archive.is_file():
        raise RuntimeError("child repeat reference is incomplete")
    return {
        "reference": str(reference.relative_to(ROOT)),
        "payload_identity_pass": baseline.same_bytes(payload, reference_payload),
        "archive_identity_pass": baseline.same_bytes(archive, reference_archive),
        "reference_payload": baseline.artifact(reference_payload),
        "reference_archive": baseline.artifact(reference_archive),
    }


def main() -> int:
    global PHASE_MARKER

    lock, source_cmix, source_head = load_program_lock()
    PHASE_MARKER = initialize_phase_marker()
    if RESULT.exists():
        raise RuntimeError(f"refusing to rotate existing result: {RESULT}")
    if not baseline.CANONICAL.is_file():
        raise RuntimeError(f"canonical input is missing: {baseline.CANONICAL}")
    if baseline.CANONICAL.stat().st_size != 1_000_000_000:
        raise RuntimeError("canonical input size mismatch")
    if baseline.sha256(baseline.CANONICAL) != baseline.EXPECTED_CANONICAL_SHA256:
        raise RuntimeError("canonical input hash mismatch")
    if not PARENT_PAYLOAD.is_file():
        raise RuntimeError("retained parent payload is missing")
    parent_payload_artifact = baseline.artifact(PARENT_PAYLOAD)
    if (
        parent_payload_artifact["bytes"] != PARENT_PAYLOAD_BYTES
        or parent_payload_artifact["sha256"] != PARENT_PAYLOAD_SHA256
    ):
        raise RuntimeError("retained parent payload identity mismatch")

    RESULT.mkdir(parents=True)
    phase("full_roundtrip", "start")

    scratch = baseline.SCRATCH_BASE / CANDIDATE_ID
    if scratch.exists():
        raise RuntimeError(f"scratch already exists: {scratch}")
    if PHASE_MARKER == scratch or scratch in PHASE_MARKER.parents:
        raise RuntimeError("phase marker must be outside candidate scratch")
    scratch.mkdir(parents=True)

    encode_dir = scratch / "encode"
    decode_dir = scratch / "decode"
    encode_dir.mkdir()
    cmix = encode_dir / "cmix"
    head = encode_dir / "head.blob"
    shutil.copy2(source_cmix, cmix)
    shutil.copy2(source_head, head)
    cmix.chmod(0o755)

    result: dict = {
        "schema": "gamma.enwiki9.memory_safe_parent_full1g_roundtrip.v1",
        "candidate_id": CANDIDATE_ID,
        "operational_status": "terminal",
        "program_lock": {
            "artifact": baseline.artifact(PROGRAM_LOCK),
            "subject": lock,
        },
        "canonical_input": baseline.artifact(baseline.CANONICAL),
        "parent_payload": parent_payload_artifact,
        "scratch_path": str(scratch),
        "phase_marker_path": str(PHASE_MARKER),
        "score_credit_bytes": 0,
        "promotion_authorized": False,
        "requires_external_resource_guard_v3_receipt": True,
    }
    peak_scratch = baseline.scratch_usage(scratch)
    error: str | None = None

    try:
        phase("encode_stage", "start")
        encode_env = {
            "PATH": os.environ.get("PATH", ""),
            "KH_BITLSTM32": str(head),
            "GAMMA_RESOURCE_PHASE_MARKERS": str(PHASE_MARKER),
        }
        result["encode"] = baseline.run_stage(
            [str(cmix), "-e", str(baseline.CANONICAL), "out.cmix"],
            encode_dir,
            encode_env,
            RESULT / "encode.stdout",
            RESULT / "encode.stderr",
            RESULT / "encode.log",
        )
        phase("encode_stage", "end", "returned")
        peak_scratch = baseline.update_peak(peak_scratch, scratch)
        if result["encode"]["returncode"] != 0:
            raise RuntimeError("encode failed")

        payload = encode_dir / "out.cmix"
        archive = encode_dir / "archive9"
        if not payload.is_file() or not archive.is_file():
            raise RuntimeError("encode did not produce payload and archive")
        shutil.copy2(payload, RESULT / "out.cmix")
        shutil.copy2(archive, RESULT / "archive9")
        payload_result = RESULT / "out.cmix"
        archive_result = RESULT / "archive9"
        result["payload"] = baseline.artifact(payload_result)
        result["archive"] = baseline.artifact(archive_result)
        result["parent_child_payload_identity_pass"] = (
            result["payload"]["bytes"] == PARENT_PAYLOAD_BYTES
            and result["payload"]["sha256"] == PARENT_PAYLOAD_SHA256
            and baseline.same_bytes(payload_result, PARENT_PAYLOAD)
        )
        result["parent_child_archive_identity_expected"] = False
        result["parent_child_archive_identity_reason"] = (
            "the memory patch changes the executable embedded in archive9"
        )
        result["counted_score_bytes"] = (
            result["archive"]["bytes"]
            + baseline.artifact(source_cmix)["bytes"]
            + baseline.artifact(source_head)["bytes"]
        )
        result["score_ceiling_pass"] = (
            result["counted_score_bytes"] <= baseline.PRIZE_CEILING_BYTES
        )

        phase("encode_scratch_cleanup", "start")
        shutil.rmtree(encode_dir)
        phase("encode_scratch_cleanup", "end", "pass")
        peak_scratch = baseline.update_peak(peak_scratch, scratch)

        decode_dir.mkdir()
        decode_archive = decode_dir / "archive9"
        shutil.copy2(archive_result, decode_archive)
        decode_archive.chmod(0o755)
        phase("decode_stage", "start")
        result["decode"] = baseline.run_stage(
            [str(decode_archive)],
            decode_dir,
            {
                "GAMMA_RESOURCE_PHASE_MARKERS": str(PHASE_MARKER),
            },
            RESULT / "decode.stdout",
            RESULT / "decode.stderr",
            RESULT / "decode.log",
        )
        phase("decode_stage", "end", "returned")
        peak_scratch = baseline.update_peak(peak_scratch, scratch)
        if result["decode"]["returncode"] != 0:
            raise RuntimeError("decode failed")

        restored = decode_dir / "enwik9"
        phase("raw_inverse_verification", "start")
        if not restored.is_file():
            raise RuntimeError("decode did not restore enwik9")
        result["restored"] = baseline.artifact(restored)
        result["raw_inverse_pass"] = (
            result["restored"]["bytes"] == 1_000_000_000
            and result["restored"]["sha256"]
            == baseline.EXPECTED_CANONICAL_SHA256
            and baseline.same_bytes(restored, baseline.CANONICAL)
        )
        phase(
            "raw_inverse_verification",
            "end",
            "pass" if result["raw_inverse_pass"] else "fail",
        )

        if REPEAT_REFERENCE is None:
            result["child_repeat_identity"] = None
        else:
            result["child_repeat_identity"] = _repeat_identity(
                REPEAT_REFERENCE, payload_result, archive_result
            )
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        result["error"] = error
        result["traceback"] = traceback.format_exc()
    finally:
        result["scratch_usage_before_cleanup"] = baseline.scratch_usage(scratch)
        peak_scratch = baseline.update_peak(peak_scratch, scratch)
        phase("final_scratch_cleanup", "start")
        cleanup_error: str | None = None
        try:
            shutil.rmtree(scratch)
        except Exception as exc:
            cleanup_error = f"{type(exc).__name__}: {exc}"
            if error is None:
                error = cleanup_error
                result["error"] = error
                result["traceback"] = traceback.format_exc()
        phase(
            "final_scratch_cleanup",
            "end",
            "fail" if cleanup_error else "pass",
        )
        result["scratch_usage_after_cleanup"] = baseline.scratch_usage(scratch)
        result["peak_scratch_usage"] = peak_scratch
        result["cleanup_pass"] = not scratch.exists()

    repeat = result.get("child_repeat_identity")
    result["operational_pass"] = bool(
        error is None
        and result.get("parent_child_payload_identity_pass")
        and result.get("raw_inverse_pass")
        and result.get("score_ceiling_pass")
        and result.get("cleanup_pass")
        and (
            repeat is None
            or (
                repeat.get("payload_identity_pass")
                and repeat.get("archive_identity_pass")
            )
        )
    )
    result["probability_stream_identity_pass"] = None
    result["probability_stream_identity_status"] = (
        "requires independently instrumented integer-probability receipt"
    )
    result["resource_compliance_pass"] = None
    result["resource_compliance_status"] = (
        "requires terminal resource-guard-receipt.v3"
    )
    phase(
        "full_roundtrip",
        "end",
        "pass" if result["operational_pass"] else "fail",
    )
    baseline.write_json(RESULT / "decision.json", result)
    return 0 if result["operational_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
