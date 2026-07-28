#!/usr/bin/env python3
"""Certify native NNCP mature headroom against identical Gamma populations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


MINIMUM_MATURE_BPM = 3000.0
MINIMUM_CUMULATIVE_RAW = 100_000_000


def load(path: Path, schema: str) -> dict[str, object]:
    value = json.loads(path.read_text())
    if value.get("schema") != schema:
        raise ValueError(f"{path}: expected schema {schema}")
    return value


def validate_common(
    nncp: dict[str, object],
    gamma: dict[str, object],
    identity: dict[str, object],
) -> None:
    if not identity.get("archive_identity") or not identity.get(
        "decoded_identity"
    ):
        raise ValueError("native teacher identity certificate did not pass")
    if nncp.get("input_sha256") != gamma.get("input_sha256"):
        raise ValueError("teacher and Gamma inputs differ")
    if nncp.get("continuous_from_raw_byte") != 0:
        raise ValueError("NNCP ledger is not continuous from byte zero")
    if gamma.get("continuous_from_raw_byte") != 0:
        raise ValueError("Gamma ledger is not continuous from byte zero")
    if nncp.get("population_id") != gamma.get("population_id"):
        raise ValueError("population identity differs")


def indexed_windows(ledger: dict[str, object]) -> dict[str, dict[str, object]]:
    windows = ledger.get("windows")
    if not isinstance(windows, list):
        raise ValueError("ledger windows must be a list")
    result: dict[str, dict[str, object]] = {}
    for window in windows:
        if not isinstance(window, dict) or not isinstance(
            window.get("window_id"), str
        ):
            raise ValueError("invalid window")
        window_id = window["window_id"]
        if window_id in result:
            raise ValueError("duplicate window ID")
        result[window_id] = window
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nncp-ledger", required=True, type=Path)
    parser.add_argument("--gamma-ledger", required=True, type=Path)
    parser.add_argument("--identity-receipt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    nncp = load(args.nncp_ledger, "nncp_native_boundary_ledger_v1")
    gamma = load(args.gamma_ledger, "gamma_boundary_ledger_v1")
    identity = load(args.identity_receipt, "nncp_native_trace_cert_v1")
    validate_common(nncp, gamma, identity)
    nncp_windows = indexed_windows(nncp)
    gamma_windows = indexed_windows(gamma)
    if set(nncp_windows) != set(gamma_windows):
        raise ValueError("teacher and Gamma window sets differ")

    rows: list[dict[str, object]] = []
    qualifying_mature = 0
    for window_id in sorted(nncp_windows):
        teacher = nncp_windows[window_id]
        parent = gamma_windows[window_id]
        for key in ("start_raw", "end_raw"):
            if teacher.get(key) != parent.get(key):
                raise ValueError(f"{window_id}: raw boundary mismatch")
        start = int(teacher["start_raw"])
        end = int(teacher["end_raw"])
        if end <= start:
            raise ValueError(f"{window_id}: invalid raw interval")
        teacher_bytes = int(teacher["exact_archive_delta_bytes"])
        gamma_bytes = int(parent["exact_archive_delta_bytes"])
        gain = gamma_bytes - teacher_bytes
        gain_bpm = gain * 1_000_000.0 / (end - start)
        mature = bool(teacher.get("mature"))
        if mature != bool(parent.get("mature")):
            raise ValueError(f"{window_id}: maturity classification mismatch")
        if mature and gain_bpm >= MINIMUM_MATURE_BPM:
            qualifying_mature += 1
        rows.append(
            {
                "end_raw": end,
                "gain_bpm": gain_bpm,
                "gamma_archive_delta_bytes": gamma_bytes,
                "mature": mature,
                "native_teacher_archive_delta_bytes": teacher_bytes,
                "native_teacher_gain_bytes": gain,
                "start_raw": start,
                "window_id": window_id,
            }
        )

    nncp_cumulative = nncp.get("cumulative")
    gamma_cumulative = gamma.get("cumulative")
    if not isinstance(nncp_cumulative, dict) or not isinstance(
        gamma_cumulative, dict
    ):
        raise ValueError("missing cumulative checkpoint")
    if nncp_cumulative.get("raw_bytes") != gamma_cumulative.get("raw_bytes"):
        raise ValueError("cumulative raw boundary mismatch")
    cumulative_raw = int(nncp_cumulative["raw_bytes"])
    cumulative_gain = int(gamma_cumulative["exact_archive_bytes"]) - int(
        nncp_cumulative["exact_archive_bytes"]
    )
    cumulative_pass = (
        cumulative_raw >= MINIMUM_CUMULATIVE_RAW and cumulative_gain > 0
    )
    authorized = qualifying_mature >= 2 and cumulative_pass

    receipt = {
        "authorization": (
            "AUTHORIZE_QUOTIENT_BUDGET_CERT"
            if authorized
            else "REJECT_TEACHER_COMPILATION"
        ),
        "cumulative": {
            "gamma_archive_bytes": gamma_cumulative["exact_archive_bytes"],
            "native_teacher_archive_bytes": nncp_cumulative[
                "exact_archive_bytes"
            ],
            "native_teacher_gain_bytes": cumulative_gain,
            "raw_bytes": cumulative_raw,
        },
        "gates": {
            "cumulative_100m_positive": cumulative_pass,
            "minimum_mature_gain_bpm": MINIMUM_MATURE_BPM,
            "qualifying_mature_windows": qualifying_mature,
            "required_mature_windows": 2,
        },
        "identity_receipt": str(args.identity_receipt),
        "schema": "nncp_mature_headroom_cert_v1",
        "score_credit_bytes": 0,
        "windows": rows,
    }
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if authorized else 3


if __name__ == "__main__":
    raise SystemExit(main())
