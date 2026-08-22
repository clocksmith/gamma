#!/usr/bin/env python3
"""Fail-closed joint decision for the frozen C/P/K/O/R/D/S 250KB screen."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
ARMS = ("C", "P", "K", "O", "R", "D", "S")
RECEIPT = re.compile(
    r"KH_DELTA_MIDAS_RECEIPT arm=(?P<arm>[PKORDS]) bits=(?P<bits>[0-9]+) "
    r"q_hash=(?P<q>[0-9a-f]{16}) state_hash=(?P<state>[0-9a-f]{16}) "
    r"adapter_hash=(?P<adapter>[0-9a-f]{16}) max_gate_q20=(?P<gate>[0-9]+) "
    r"max_logit_q20=(?P<logit>[0-9]+) finite=(?P<finite>[01])"
)


def candidate_id(arm: str, ppm_always_purge: bool) -> str:
    if ppm_always_purge:
        return f"cmix_obias_bithead_delta_midas512_ppm0_disk_{arm.lower()}_q0_v5"
    return f"cmix_obias_bithead_delta_midas512_{arm.lower()}_q0_v2"


def load_decision(arm: str, ppm_always_purge: bool) -> dict[str, object]:
    expected_id = candidate_id(arm, ppm_always_purge)
    path = ROOT / "results" / expected_id / "decision.json"
    value = json.loads(path.read_text())
    if value.get("candidate_id") != expected_id:
        raise ValueError(f"candidate identity mismatch for {arm}")
    return value


def stage_receipt(decision: dict[str, object], stage: str) -> dict[str, object] | None:
    execution = decision.get("execution", {})
    value = execution.get(stage, {}) if isinstance(execution, dict) else {}
    stderr = value.get("stderr_tail", "") if isinstance(value, dict) else ""
    matches = [match.groupdict() for match in RECEIPT.finditer(str(stderr))]
    if not matches:
        return None
    chosen = max(matches, key=lambda item: int(item["bits"]))
    return {
        "arm": chosen["arm"],
        "bits": int(chosen["bits"]),
        "q_hash": chosen["q"],
        "state_hash": chosen["state"],
        "adapter_hash": chosen["adapter"],
        "max_gate_q20": int(chosen["gate"]),
        "max_logit_q20": int(chosen["logit"]),
        "finite": chosen["finite"] == "1",
    }


def all_resources_within(value: object) -> bool:
    found: list[bool] = []

    def visit(node: object) -> None:
        if isinstance(node, dict):
            resource = node.get("resource")
            if isinstance(resource, dict) and "within_limit" in resource:
                found.append(resource.get("within_limit") is True)
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return bool(found) and all(found)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ppm-always-purge", action="store_true")
    args = parser.parse_args()
    if args.ppm_always_purge:
        result = ROOT / "results" / "cmix_obias_bithead_delta_midas512_ppm0_joint_q0_v3"
    else:
        result = ROOT / "results" / "cmix_obias_bithead_delta_midas512_joint_q0_v2"
    if result.exists():
        raise FileExistsError(f"refusing to overwrite {result}")
    decisions = {arm: load_decision(arm, args.ppm_always_purge) for arm in ARMS}
    receipts = {
        arm: {
            stage: stage_receipt(decisions[arm], stage)
            for stage in ("encode1", "encode2", "bare_decode")
        }
        for arm in ARMS
        if arm != "C"
    }
    payload_bytes = {
        arm: int(decisions[arm]["payload"]["bytes"]) for arm in ARMS
    }
    counted_bytes = {
        arm: int(decisions[arm]["archive"]["bytes"])
        + int(decisions[arm]["program_accounting"]["total_bytes"])
        for arm in ARMS
    }
    exact = {
        arm: (
            decisions[arm].get("integrity", {}).get("raw_roundtrip_exact") is True
            and decisions[arm]
            .get("integrity", {})
            .get("repeat_archive_and_payload_byte_identical")
            is True
        )
        for arm in ARMS
    }
    receipt_sync: dict[str, bool] = {}
    for arm in ARMS:
        if arm == "C":
            continue
        rows = receipts[arm]
        complete = all(rows[stage] is not None for stage in rows)
        receipt_sync[arm] = bool(
            complete
            and rows["encode1"]["arm"] == arm
            and rows["encode1"]["q_hash"] == rows["encode2"]["q_hash"]
            and rows["encode1"]["q_hash"] == rows["bare_decode"]["q_hash"]
            and rows["encode1"]["state_hash"] == rows["encode2"]["state_hash"]
            and rows["encode1"]["state_hash"] == rows["bare_decode"]["state_hash"]
        )

    clean_parent_identity = payload_bytes["C"] == payload_bytes["P"]
    p_k_identity = bool(
        receipt_sync.get("P")
        and receipt_sync.get("K")
        and receipts["P"]["encode1"]["q_hash"]
        == receipts["K"]["encode1"]["q_hash"]
        and receipts["P"]["encode1"]["state_hash"]
        == receipts["K"]["encode1"]["state_hash"]
        and payload_bytes["P"] == payload_bytes["K"]
    )
    finite = all(
        receipts[arm]["encode1"] is not None
        and receipts[arm]["encode1"]["finite"]
        for arm in ARMS
        if arm != "C"
    )
    control_fields = {
        "O": "max_logit_q20",
        "R": "max_gate_q20",
        "D": "max_gate_q20",
        "S": "max_gate_q20",
    }
    controls_live = all(
        receipts[arm]["encode1"] is not None
        and receipts[arm]["encode1"][field] > 0
        for arm, field in control_fields.items()
    )
    d_beats_controls = all(
        payload_bytes["D"] < payload_bytes[arm]
        for arm in ("P", "K", "O", "R", "S")
    )
    def disk_scratch_within(decision: dict[str, object]) -> bool:
        overlay = decision.get("gamma_overlay", {})
        boundary = overlay.get("scratch_boundary", {}) if isinstance(overlay, dict) else {}
        try:
            allocated = int(
                decision.get("scratch_peak", {}).get("allocated_bytes", -1)
            )
        except (TypeError, ValueError):
            return False
        return bool(
            isinstance(boundary, dict)
            and boundary.get("memory_backed") is False
            and boundary.get("filesystem") not in {"tmpfs", "ramfs"}
            and 0 <= allocated <= 100_000_000_000
        )

    resources_ok = all(all_resources_within(decisions[arm]) for arm in ARMS)
    disk_scratch_ok = all(disk_scratch_within(decisions[arm]) for arm in ARMS)
    added_program_bytes = (
        int(decisions["D"]["program_accounting"]["total_bytes"])
        - int(decisions["C"]["program_accounting"]["total_bytes"])
    )
    package_ok = added_program_bytes <= 65_536
    gates = {
        "all_roundtrips_and_repeats_exact": all(exact.values()),
        "clean_parent_payload_identity": clean_parent_identity,
        "p_k_probability_state_payload_identity": p_k_identity,
        "all_arm_encode_decode_receipts_synchronized": all(receipt_sync.values()),
        "finite_adapter": finite,
        "controls_live": controls_live,
        "d_payload_beats_p_k_o_r_s": d_beats_controls,
        "all_process_tree_rss_within_limit": resources_ok,
        "disk_scratch_and_storage_within_limit": disk_scratch_ok,
        "incremental_package_within_65536": package_ok,
    }
    passed = all(gates.values())
    result = {
        "schema": (
            "gamma.enwiki9.cmix-obias-bithead-delta-midas512-ppm0-joint-disk-q0-v5"
            if args.ppm_always_purge
            else "gamma.enwiki9.cmix-obias-bithead-delta-midas512-joint-q0-v2"
        ),
        "candidate_id": (
            "cmix_obias_bithead_delta_midas512_ppm0_joint_disk_q0_v5"
            if args.ppm_always_purge
            else "cmix_obias_bithead_delta_midas512_joint_q0_v2"
        ),
        "scope_raw_bytes": 250_000,
        "claim_boundary": "Joint opening-250KB diagnostic only; zero compression credit.",
        "score_credit_bytes": 0,
        "payload_bytes": payload_bytes,
        "counted_bytes": counted_bytes,
        "payload_savings_d_vs_p": payload_bytes["P"] - payload_bytes["D"],
        "counted_savings_d_vs_p": counted_bytes["P"] - counted_bytes["D"],
        "incremental_program_bytes_d_vs_clean": added_program_bytes,
        "receipts": receipts,
        "gates": gates,
        "overall_pass": passed,
        "promotion_authorized": passed,
        "next_scope_if_pass": "1MB prospectively frozen successor",
        "ppm_always_purge": args.ppm_always_purge,
    }
    result.mkdir(parents=True)
    (result / "decision.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({"event": "joint_terminal", "overall_pass": passed}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
