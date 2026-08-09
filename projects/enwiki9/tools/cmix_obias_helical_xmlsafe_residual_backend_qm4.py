#!/usr/bin/env python3
"""Run the frozen QM4 residual through the matched native cmix-obias backend."""

from __future__ import annotations

import hashlib
import json
import lzma
import os
from pathlib import Path
import struct
import subprocess
import time


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_helical_xmlsafe_prefix_qm4_v1"
RESULT_DIR = ROOT / "results" / CANDIDATE_ID
DECISION_PATH = RESULT_DIR / "decision.json"
RECEIPT_PATH = RESULT_DIR / "residual_backend_receipt.json"
SOURCE_PACKAGE_PATH = RESULT_DIR / "incremental_source_package.lzma"
ARTIFACT_ROOT = Path("/home/x/enwiki9-nonproof/results") / CANDIDATE_ID
BACKEND_DIR = ARTIFACT_ROOT / "backend/residual"
CMIX_PATH = BACKEND_DIR / "cmix"
HEAD_PATH = ARTIFACT_ROOT / "head.blob"
RESIDUAL_PATH = ARTIFACT_ROOT / "residual.bin"
OUT_PATH = BACKEND_DIR / "out.cmix"
ARCHIVE_PATH = BACKEND_DIR / "archive9"
LOG_PATH = BACKEND_DIR / "progress.log"
QM4_SOURCE_PATH = ROOT / "tools/cmix_obias_helical_xmlsafe_prefix_qm4.py"
DRIVER_SOURCE_PATH = Path(__file__).resolve()
EXPECTED_CMIX_SHA256 = "aee602b8145f7f04c9a6ea9107cf44bc5c94677723101eec3288a78377ddad97"
EXPECTED_HEAD_SHA256 = "35cd24fed87c3409994abf5573b5697be19ea03b5ece0928b69b1cdc4f3b6078"
EXPECTED_RESIDUAL_SHA256 = "e550869c0870630f70da36fb472f056375eaf1dfc0962b4730e3fe6caadd7ba4"
EXPECTED_RESIDUAL_BYTES = 249_407_080
BASELINE_ARCHIVE_BYTES = 33_554_085
BASELINE_ARCHIVE_SHA256 = "ed5a5b6c5f0e6b35171204918e5a291a4c7119a7ba7abd24e0b29c49d0238f09"
FIXED_WRAPPER_OVERHEAD_BYTES = 291_697
LEDGER_BYTES = 36_640
POLL_SECONDS = 2.0
CHUNK_BYTES = 8 << 20


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK_BYTES), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def build_source_package() -> dict[str, object]:
    payload = bytearray(b"QM4SP1\0\0")
    for path in sorted((QM4_SOURCE_PATH, DRIVER_SOURCE_PATH), key=lambda item: item.name):
        name = path.name.encode("ascii")
        data = path.read_bytes()
        payload.extend(struct.pack("<IQ", len(name), len(data)))
        payload.extend(name)
        payload.extend(data)
    SOURCE_PACKAGE_PATH.write_bytes(lzma.compress(bytes(payload), preset=9 | lzma.PRESET_EXTREME))
    return artifact(SOURCE_PACKAGE_PATH)


def write_receipt(receipt: dict[str, object]) -> None:
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    decision = json.loads(DECISION_PATH.read_text())
    decision["backend"].update({
        "residual_receipt": str(RECEIPT_PATH.relative_to(ROOT)),
        "residual_archive_bytes": receipt.get("residual_archive_bytes"),
        "gross_archive_gain_bytes": receipt.get("gross_archive_gain_bytes"),
        "incremental_source_bytes": receipt.get("incremental_source_bytes"),
        "fully_paid_net_gain_bytes": receipt.get("fully_paid_net_gain_bytes"),
    })
    DECISION_PATH.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")


def stop_process(process: subprocess.Popen[bytes]) -> int:
    process.terminate()
    try:
        return process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        process.kill()
        return process.wait()


def main() -> int:
    if CMIX_PATH.stat().st_size != 468_485 or sha256_file(CMIX_PATH) != EXPECTED_CMIX_SHA256:
        raise ValueError("matched cmix executable mismatch")
    if HEAD_PATH.stat().st_size != 23_002 or sha256_file(HEAD_PATH) != EXPECTED_HEAD_SHA256:
        raise ValueError("matched head asset mismatch")
    if RESIDUAL_PATH.stat().st_size != EXPECTED_RESIDUAL_BYTES:
        raise ValueError("frozen residual size mismatch")
    if sha256_file(RESIDUAL_PATH) != EXPECTED_RESIDUAL_SHA256:
        raise ValueError("frozen residual hash mismatch")
    for path in (OUT_PATH, ARCHIVE_PATH, LOG_PATH):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite {path}")
    source_package = build_source_package()
    source_bytes = int(source_package["bytes"])
    payload_abort_threshold = (
        BASELINE_ARCHIVE_BYTES
        - FIXED_WRAPPER_OVERHEAD_BYTES
        - LEDGER_BYTES
        - source_bytes
    )
    environment = os.environ.copy()
    environment["KH_BITLSTM32"] = str(HEAD_PATH)
    environment["CMIX_PPM_RSS_MB"] = "8500"
    started = time.monotonic()
    with LOG_PATH.open("xb") as log:
        process = subprocess.Popen(
            ["./cmix", "-e", str(RESIDUAL_PATH), "out.cmix"],
            cwd=BACKEND_DIR,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        aborted = False
        observed_payload_bytes = 0
        while process.poll() is None:
            if OUT_PATH.exists():
                observed_payload_bytes = OUT_PATH.stat().st_size
                if observed_payload_bytes >= payload_abort_threshold:
                    aborted = True
                    stop_process(process)
                    break
            time.sleep(POLL_SECONDS)
        returncode = process.wait()
    elapsed = time.monotonic() - started
    common: dict[str, object] = {
        "schema": "enwiki9_cmix_obias_helical_xmlsafe_qm4_residual_backend_receipt_v1",
        "candidate_id": CANDIDATE_ID,
        "command": ["./cmix", "-e", str(RESIDUAL_PATH), "out.cmix"],
        "working_directory": str(BACKEND_DIR),
        "environment": {"KH_BITLSTM32": str(HEAD_PATH), "CMIX_PPM_RSS_MB": "8500"},
        "cmix": artifact(CMIX_PATH),
        "head": artifact(HEAD_PATH),
        "residual": artifact(RESIDUAL_PATH),
        "baseline_archive_bytes": BASELINE_ARCHIVE_BYTES,
        "baseline_archive_sha256": BASELINE_ARCHIVE_SHA256,
        "fixed_wrapper_overhead_bytes": FIXED_WRAPPER_OVERHEAD_BYTES,
        "ledger_bytes": LEDGER_BYTES,
        "incremental_source_package": source_package,
        "incremental_source_bytes": source_bytes,
        "payload_abort_threshold_bytes": payload_abort_threshold,
        "maximum_observed_payload_bytes": observed_payload_bytes,
        "returncode": returncode,
        "elapsed_seconds_diagnostic": elapsed,
    }
    if aborted:
        receipt = common | {
            "verdict": "retire_monotone_nonpositive",
            "residual_archive_bytes": None,
            "gross_archive_gain_bytes": None,
            "fully_paid_net_gain_bytes": None,
            "claim_boundary": (
                "Residual payload crossed the frozen monotone nonpositive threshold. "
                "No complete residual archive or roundtrip claim."
            ),
        }
        write_receipt(receipt)
        print(json.dumps(receipt, sort_keys=True))
        return 0
    if returncode != 0:
        receipt = common | {
            "verdict": "backend_failed",
            "residual_archive_bytes": None,
            "gross_archive_gain_bytes": None,
            "fully_paid_net_gain_bytes": None,
            "claim_boundary": "Backend process failed before matched archive adjudication.",
        }
        write_receipt(receipt)
        print(json.dumps(receipt, sort_keys=True))
        return 1
    if not OUT_PATH.is_file() or not ARCHIVE_PATH.is_file():
        raise FileNotFoundError("backend completed without payload and archive")
    residual_payload_bytes = OUT_PATH.stat().st_size
    residual_archive_bytes = ARCHIVE_PATH.stat().st_size
    if residual_archive_bytes - residual_payload_bytes != FIXED_WRAPPER_OVERHEAD_BYTES:
        raise ValueError("fixed package overhead did not reproduce")
    gross_gain = BASELINE_ARCHIVE_BYTES - residual_archive_bytes
    fully_paid_gain = gross_gain - LEDGER_BYTES - source_bytes
    receipt = common | {
        "verdict": "positive_matched_backend" if fully_paid_gain > 0 else "retire_fully_paid_nonpositive",
        "payload": artifact(OUT_PATH),
        "archive": artifact(ARCHIVE_PATH),
        "residual_payload_bytes": residual_payload_bytes,
        "residual_archive_bytes": residual_archive_bytes,
        "gross_archive_gain_bytes": gross_gain,
        "fully_paid_net_gain_bytes": fully_paid_gain,
        "roundtrip_verified": False,
        "claim_boundary": (
            "Exact matched residual encode and fully paid prefix delta only. "
            "Decode, inverse, isolated timing, full-corpus transfer, and score remain unproved."
        ),
    }
    write_receipt(receipt)
    print(json.dumps({
        "verdict": receipt["verdict"],
        "residual_payload_bytes": residual_payload_bytes,
        "residual_archive_bytes": residual_archive_bytes,
        "gross_archive_gain_bytes": gross_gain,
        "ledger_bytes": LEDGER_BYTES,
        "incremental_source_bytes": source_bytes,
        "fully_paid_net_gain_bytes": fully_paid_gain,
        "archive_sha256": receipt["archive"]["sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
