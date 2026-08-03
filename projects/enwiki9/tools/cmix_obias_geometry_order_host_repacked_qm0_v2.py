#!/usr/bin/env python3
"""Host-repacked infrastructure successor for the cmix-obias geometry Qm0."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import struct
import tempfile
from typing import Any

import cmix_obias_geometry_order_substitution_qm0 as base


CANDIDATE_ID = "cmix_obias_geometry_order_host_repacked_qm0_v2"
SCHEMA = "cmix_obias_geometry_order_host_repacked_qm0_decision_v2"
RAW_DICT_BYTES = 411_996
RAW_DICT_SHA256 = "4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a"
ATTEMPT_V1_JOB = "20260803T020929Z_31a36cad90"


def compress_asset(
    *,
    raw_executable: bytes,
    source: pathlib.Path,
    output: pathlib.Path,
    workspace: pathlib.Path,
    env: dict[str, str],
) -> dict[str, Any]:
    workspace.mkdir(parents=True)
    executable = workspace / "cmix_orig"
    executable.write_bytes(raw_executable)
    executable.chmod(0o755)
    base.run_checked(
        [str(executable), "-c", str(source), str(output)],
        cwd=workspace,
        env=env,
    )
    (workspace / "ppm.temp").unlink(missing_ok=True)
    return {
        "bytes": output.stat().st_size,
        "sha256": base.sha256_file(output),
    }


def build_host_package(
    *,
    arm: str,
    workspace: pathlib.Path,
    raw_executable: bytes,
    comp_dict: pathlib.Path,
    raw_order: bytes,
    env: dict[str, str],
) -> tuple[pathlib.Path, dict[str, Any]]:
    workspace.mkdir(parents=True)
    executable = workspace / "cmix_orig"
    executable.write_bytes(raw_executable)
    executable.chmod(0o755)
    order_path = workspace / "order.txt"
    order_path.write_bytes(raw_order)
    comp_order = workspace / "comp_order"
    base.run_checked(
        [str(executable), "-c", str(order_path), str(comp_order)],
        cwd=workspace,
        env=env,
    )
    (workspace / "ppm.temp").unlink(missing_ok=True)
    base.run_checked(
        [
            str(executable),
            "-h",
            str(comp_dict.stat().st_size),
            str(comp_order.stat().st_size),
            "0",
        ],
        cwd=workspace,
        env=env,
    )
    header = workspace / "header.dat"
    header_bytes = header.read_bytes()
    if len(header_bytes) != 16:
        raise RuntimeError(f"{arm} header is not 16 bytes")
    expected_header = (comp_dict.stat().st_size, comp_order.stat().st_size, 0, 0)
    if struct.unpack("<4i", header_bytes) != expected_header:
        raise RuntimeError(f"{arm} header mismatch")
    package = workspace / "cmix"
    package.write_bytes(
        raw_executable + comp_dict.read_bytes() + comp_order.read_bytes() + header_bytes
    )
    package.chmod(0o755)
    return package, {
        "raw_order_bytes": len(raw_order),
        "raw_order_sha256": hashlib.sha256(raw_order).hexdigest(),
        "comp_order_bytes": comp_order.stat().st_size,
        "comp_order_sha256": base.sha256_file(comp_order),
        "comp_dict_bytes": comp_dict.stat().st_size,
        "comp_dict_sha256": base.sha256_file(comp_dict),
        "packaged_cmix_bytes": package.stat().st_size,
        "packaged_cmix_sha256": base.sha256_file(package),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--donor-root", type=pathlib.Path, required=True)
    parser.add_argument(
        "--input", type=pathlib.Path, default=base.PROJECT_ROOT / "data" / "enwik9"
    )
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=base.PROJECT_ROOT / "results" / CANDIDATE_ID,
    )
    args = parser.parse_args()

    base.CANDIDATE_ID = CANDIDATE_ID
    donor_root = args.donor_root.resolve()
    input_path = args.input.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if input_path.stat().st_size != base.FULL_INPUT_BYTES:
        raise RuntimeError(f"full input size mismatch: {input_path.stat().st_size}")
    if base.sha256_file(input_path) != base.FULL_INPUT_SHA256:
        raise RuntimeError("full enwik9 hash mismatch")
    paths, raw_executable = base.verify_donor(donor_root)
    raw_dictionary = donor_root / "cmix-obias" / "dictionary" / "english.dic"
    base.require_file(raw_dictionary, RAW_DICT_BYTES, RAW_DICT_SHA256)

    asset_env = os.environ.copy()
    asset_env["KH_BITLSTM32"] = str(paths["head"])
    asset_env.pop("CMIX_PPM_RSS_MB", None)

    with tempfile.TemporaryDirectory(prefix=f"{CANDIDATE_ID}_") as temporary_text:
        temporary = pathlib.Path(temporary_text)
        prefix_path = temporary / "enwik7"
        base.write_prefix(input_path, prefix_path)
        data = prefix_path.read_bytes()

        geometry_order_a, geometry_counts = base.generate_order(data, "geometry")
        geometry_order_b, geometry_counts_b = base.generate_order(data, "geometry")
        if geometry_order_a != geometry_order_b or geometry_counts != geometry_counts_b:
            raise RuntimeError("G0 raw order rebuild is not byte-identical")

        local_dict_a = temporary / "dict_a" / "comp_dict"
        local_dict_b = temporary / "dict_b" / "comp_dict"
        dict_receipt_a = compress_asset(
            raw_executable=raw_executable,
            source=raw_dictionary,
            output=local_dict_a,
            workspace=local_dict_a.parent,
            env=asset_env,
        )
        dict_receipt_b = compress_asset(
            raw_executable=raw_executable,
            source=raw_dictionary,
            output=local_dict_b,
            workspace=local_dict_b.parent,
            env=asset_env,
        )
        dictionary_replay_identity = (
            dict_receipt_a == dict_receipt_b
            and local_dict_a.read_bytes() == local_dict_b.read_bytes()
        )
        if not dictionary_replay_identity:
            raise RuntimeError("host-local dictionary stream is not deterministic")

        b0_package, b0_package_receipt = build_host_package(
            arm="B0",
            workspace=temporary / "package_B0",
            raw_executable=raw_executable,
            comp_dict=local_dict_a,
            raw_order=paths["raw_order"].read_bytes(),
            env=asset_env,
        )
        g0_package, g0_package_receipt = build_host_package(
            arm="G0",
            workspace=temporary / "package_G0",
            raw_executable=raw_executable,
            comp_dict=local_dict_a,
            raw_order=geometry_order_a,
            env=asset_env,
        )

        b0 = base.run_arm(
            arm="B0",
            package=b0_package,
            input_path=prefix_path,
            head_path=paths["head"],
            root=temporary,
        )
        g0 = base.run_arm(
            arm="G0",
            package=g0_package,
            input_path=prefix_path,
            head_path=paths["head"],
            root=temporary,
        )
        gross_gain = b0["archive9_bytes"] - g0["archive9_bytes"]

        t0: dict[str, Any] | None = None
        t0_package_receipt: dict[str, Any] | None = None
        repeat: dict[str, Any] | None = None
        control_pass = False
        determinism_pass = False
        if gross_gain >= base.GROSS_GATE_BYTES:
            title_order, title_counts = base.generate_order(data, "title")
            t0_package, t0_package_receipt = build_host_package(
                arm="T0",
                workspace=temporary / "package_T0",
                raw_executable=raw_executable,
                comp_dict=local_dict_a,
                raw_order=title_order,
                env=asset_env,
            )
            t0_package_receipt["page_counts"] = title_counts
            t0 = base.run_arm(
                arm="T0",
                package=t0_package,
                input_path=prefix_path,
                head_path=paths["head"],
                root=temporary,
            )
            control_pass = g0["archive9_bytes"] < t0["archive9_bytes"]
            repeat = base.repeated_encode(
                package=g0_package,
                input_path=prefix_path,
                head_path=paths["head"],
                expected=g0,
                root=temporary,
            )
            determinism_pass = bool(repeat["byte_identical"])

        verdict = (
            "AUTHORIZE_SOURCE_CHILD"
            if gross_gain >= base.GROSS_GATE_BYTES and control_pass and determinism_pass
            else "REJECT"
        )
        actual_order_asset_saving_ceiling = (
            b0_package_receipt["comp_order_bytes"] - base.ALGORITHMIC_SOURCE_ALLOWANCE
        )
        decision = {
            "candidate_id": CANDIDATE_ID,
            "schema": SCHEMA,
            "status": "terminal",
            "scope": {
                "bytes": base.SCOPE_BYTES,
                "sha256": base.SCOPE_SHA256,
                "population": "canonical opening 10M",
            },
            "infrastructure_predecessor": {
                "candidate_id": "cmix_obias_geometry_order_substitution_qm0_v1",
                "job_id": ATTEMPT_V1_JOB,
                "classification": "precompressed_asset_dialect_failure",
                "scientific_verdict": None,
            },
            "inputs": {
                "donor_commit": base.DONOR_COMMIT,
                "full_input_bytes": base.FULL_INPUT_BYTES,
                "full_input_sha256": base.FULL_INPUT_SHA256,
                "raw_cmix_bytes": base.RAW_CMIX_BYTES,
                "raw_cmix_sha256": base.RAW_CMIX_SHA256,
                "raw_dictionary_bytes": RAW_DICT_BYTES,
                "raw_dictionary_sha256": RAW_DICT_SHA256,
                "raw_public_order_bytes": base.RAW_PUBLIC_ORDER_BYTES,
                "raw_public_order_sha256": base.RAW_PUBLIC_ORDER_SHA256,
                "head_bytes": base.HEAD_BYTES,
                "head_sha256": base.HEAD_SHA256,
            },
            "host_repack": {
                "dictionary_a": dict_receipt_a,
                "dictionary_b": dict_receipt_b,
                "dictionary_replay_identity": dictionary_replay_identity,
                "head_enabled_for_asset_encode_and_decode": True,
            },
            "orders": {
                "public": b0_package_receipt,
                "geometry": {**g0_package_receipt, "page_counts": geometry_counts},
                "title": t0_package_receipt,
            },
            "arms": {"B0": b0, "G0": g0, "T0": t0, "G0_repeat": repeat},
            "accounting": {
                "b0_archive_bytes": b0["archive9_bytes"],
                "g0_archive_bytes": g0["archive9_bytes"],
                "gross_archive_gain_10m_bytes": gross_gain,
                "gross_archive_gain_bytes_per_million": gross_gain / 10.0,
                "gross_gate_bytes": base.GROSS_GATE_BYTES,
                "algorithmic_source_allowance_bytes": base.ALGORITHMIC_SOURCE_ALLOWANCE,
                "host_b0_comp_order_bytes": b0_package_receipt["comp_order_bytes"],
                "actual_order_asset_saving_ceiling_bytes": actual_order_asset_saving_ceiling,
                "full_1g_projection_valid": False,
                "projection_score_credit_bytes": 0,
            },
            "gates": {
                "dictionary_replay_identity": dictionary_replay_identity,
                "parent_roundtrip": b0["roundtrip_ok"],
                "geometry_order_rebuild_identity": geometry_order_a == geometry_order_b,
                "geometry_roundtrip": g0["roundtrip_ok"],
                "geometry_gross_gate": gross_gain >= base.GROSS_GATE_BYTES,
                "geometry_beats_title": control_pass,
                "geometry_repeat_identity": determinism_pass,
            },
            "decision": {
                "verdict": verdict,
                "scientific_valid": True,
                "score_credit_bytes": 0,
                "forecast_change_authorized": False,
                "source_child_authorized": verdict == "AUTHORIZE_SOURCE_CHILD",
                "next_action": (
                    "Materialize only the frozen source-level geometry generator child and one distant replay."
                    if verdict == "AUTHORIZE_SOURCE_CHILD"
                    else "Retire this exact geometry-order substitution on the cmix-obias donor without rescue sweeps."
                ),
            },
        }
        base.atomic_json(output_dir / "decision.json", decision)
        print(json.dumps(decision, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
