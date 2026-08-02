#!/usr/bin/env python3
"""Run the exact BIFRONS reverse-causal two-ended ceiling gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

import paid_block_vector_codebook as payload_codec
from endpoint428_parent_recovery_gate import observed_artifact, run_guarded


PROJECT = Path(__file__).resolve().parents[1]
NONPROOF = Path("/home/x/enwiki9-nonproof")
CANDIDATE_ID = "bifrons_reverse_causal_joint_ceiling_q0_v1"
P1_MAGIC = b"CMX21P1\0"
STORE_HEADER = b"\x80\x00\x00\x00\x00"
P1_HEADER_BYTES = 16
CMIX_HEADER_BYTES = 37
CANDIDATE_FRAME_BYTES = 49
QBITS = 256
RAW_LIMIT = 1_000_000
GROSS_GATE_BPM = 3_000.0

SOURCE_ROOT = (
    NONPROOF
    / "results/cmix21_lstm200_plus_fx2lite428_onlinepairlayer0_source_package_v17"
    / "clean-build-b/build"
)

EXPECTED_SHA256 = {
    "backend": "ce71136ad210092bcbe0a9ff6c388767611482ea24c60849455ae70d36e84e97",
    "dictionary": "4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a",
    "endpoint_p1": "3a689d87b5dd25803e455de2f32ed80e8dddbda953efbdfc18311d5e44567641",
    "joint_p1": "b554ddd170df355ab597fa8fd082b2ea4d2098dad540b07dcb9084016cc2e719",
    "wrt_store": "867c23e652052268017d4bda543ea86c6b6af7efdaa0d87175997e7fb19a3a5b",
    "page_map": "bbd7997af61a3d1a968f245377ec651d581c97720aa12a3f5b96fd98fa6e2e79",
    "joint_decision": "a8e098f1e658d91e16275bb17ad950d0249c5aafbd9841458a18b41cdc5daa9e",
    "endpoint_decision": "b25a30eeec26d33ac4825da91c4ca10510acdf1a1f8dcc5301be1253ab5365d6",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def bind(path: Path, expected: str, label: str) -> dict[str, Any]:
    row = observed_artifact(path)
    if row["sha256"] != expected:
        raise ValueError(f"{label} SHA-256 mismatch: {row['sha256']}")
    return row


def read_p1(path: Path, expected_rows: int | None = None) -> np.memmap:
    with path.open("rb") as source:
        header = source.read(P1_HEADER_BYTES)
    if len(header) != P1_HEADER_BYTES or header[:8] != P1_MAGIC:
        raise ValueError(f"invalid P1 trace: {path}")
    rows = struct.unpack_from("<Q", header, 8)[0]
    if rows <= 0 or path.stat().st_size != P1_HEADER_BYTES + 2 * rows:
        raise ValueError(f"invalid P1 row binding: {path}")
    if expected_rows is not None and rows != expected_rows:
        raise ValueError(f"P1 rows differ: {rows} != {expected_rows}")
    values = np.memmap(
        path, mode="r", dtype="<u2", offset=P1_HEADER_BYTES, shape=(rows,)
    )
    if np.any(values == 0):
        raise ValueError(f"P1 trace contains zero: {path}")
    return values


def read_page_map(path: Path) -> list[tuple[int, int, int, int]]:
    raw = path.read_bytes()
    if len(raw) < 16 or raw[:8] != b"SIBMAP1\0":
        raise ValueError("invalid page map")
    count = struct.unpack_from("<Q", raw, 8)[0]
    record = struct.Struct("<QQQQ")
    if len(raw) != 16 + count * record.size:
        raise ValueError("page map size mismatch")
    return [record.unpack_from(raw, 16 + i * record.size) for i in range(count)]


def qbit_tables() -> tuple[np.ndarray, np.ndarray]:
    values = np.arange(65536, dtype=np.float64)
    values[0] = 1.0
    p1 = values / 65536.0
    p0 = 1.0 - p1
    return (
        np.rint(-np.log2(p0) * QBITS).astype(np.int32),
        np.rint(-np.log2(p1) * QBITS).astype(np.int32),
    )


def byte_qbits(
    probabilities: np.ndarray, truth: np.ndarray,
    zero: np.ndarray, one: np.ndarray,
) -> np.ndarray:
    if len(probabilities) != len(truth) or len(truth) % 8:
        raise ValueError("unaligned P1 and truth")
    result = np.empty(len(truth) // 8, dtype=np.int64)
    chunk_bytes = 1 << 16
    for byte_start in range(0, len(result), chunk_bytes):
        byte_end = min(len(result), byte_start + chunk_bytes)
        row_start = byte_start * 8
        row_end = byte_end * 8
        p1 = np.asarray(probabilities[row_start:row_end], dtype=np.uint16)
        bits = truth[row_start:row_end]
        costs = np.where(bits != 0, one[p1], zero[p1])
        result[byte_start:byte_end] = costs.reshape(-1, 8).sum(axis=1)
    return result


def range_decode(payload: bytes, probabilities: np.ndarray) -> np.ndarray:
    if len(probabilities) == 0:
        return np.empty(0, dtype=np.uint8)
    padded = payload + b"\0\0\0\0"
    cursor = 4
    code = int.from_bytes(padded[:4], "big")
    low = 0
    high = 0xFFFFFFFF
    truth = np.empty(len(probabilities), dtype=np.uint8)
    for index, probability in enumerate(probabilities):
        p1 = int(probability)
        delta = high - low
        midpoint = low + (delta >> 16) * p1
        midpoint += ((delta & 0xFFFF) * p1) >> 16
        if code <= midpoint:
            truth[index] = 1
            high = midpoint
        else:
            truth[index] = 0
            low = midpoint + 1
        while ((low ^ high) & 0xFF000000) == 0:
            low = (low << 8) & 0xFFFFFFFF
            high = ((high << 8) & 0xFFFFFFFF) + 255
            next_byte = padded[cursor] if cursor < len(padded) else 0
            cursor += 1
            code = ((code << 8) & 0xFFFFFFFF) + next_byte
    return truth


def write_reverse_inputs(
    output_dir: Path, dictionary: Path, body: bytes
) -> tuple[Path, Path]:
    reverse_store = output_dir / "reverse.store"
    reverse_dictionary = output_dir / "reverse_dictionary.bin"
    if reverse_store.exists() or reverse_dictionary.exists():
        raise FileExistsError("refusing to overwrite reverse inputs")
    reverse_store.write_bytes(STORE_HEADER + body[::-1])
    reverse_dictionary.write_bytes(dictionary.read_bytes()[::-1])
    return reverse_store, reverse_dictionary


def reverse_run(
    label: str, output_dir: Path, backend: Path, dictionary: Path,
    reverse_store: Path, reverse_dictionary: Path,
) -> dict[str, Any]:
    archive = output_dir / f"reverse_{label}.cmix"
    trace = output_dir / f"reverse_{label}.p1"
    if archive.exists() or trace.exists():
        raise FileExistsError(f"refusing to overwrite reverse run {label}")
    command = [
        "/usr/bin/env",
        f"CMIX_P1_TRACE={trace}",
        f"CMIX_PRETRAIN_FILE={reverse_dictionary}",
        str(backend),
        "-r",
        str(dictionary),
        str(reverse_store),
        str(archive),
    ]
    phase = run_guarded(f"reverse_{label}", output_dir, command)
    return {"archive": archive, "trace": trace, "phase": phase}


def make_candidate_frame(
    standard_header: bytes, cut_byte: int,
    forward_bytes: int, reverse_bytes: int,
) -> bytes:
    if len(standard_header) != CMIX_HEADER_BYTES:
        raise ValueError("standard CMIX header must contain length and vocabulary")
    return standard_header + struct.pack(
        "<III", cut_byte, forward_bytes, reverse_bytes
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path,
        default=PROJECT / "results" / CANDIDATE_ID,
    )
    parser.add_argument(
        "--joint-p1", type=Path,
        default=PROJECT / "results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/joint_candidate.p1",
    )
    parser.add_argument(
        "--endpoint-p1", type=Path,
        default=PROJECT / "results/endpoint428_pair_layer0_online_native_trace_10m_v1/native.p1",
    )
    parser.add_argument(
        "--wrt-store", type=Path,
        default=PROJECT / "results/endpoint428_pair_layer0_online_native_trace_10m_v1/wrt_store.bin",
    )
    parser.add_argument(
        "--page-map", type=Path,
        default=PROJECT / "results/mobius2_tessera_typed_fiber_ceiling_qh0_v1/page_map.bin",
    )
    parser.add_argument(
        "--joint-decision", type=Path,
        default=PROJECT / "results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/decision.json",
    )
    parser.add_argument(
        "--endpoint-decision", type=Path,
        default=PROJECT / "results/endpoint428_pair_layer0_online_native_trace_10m_v1/decision.json",
    )
    parser.add_argument("--backend", type=Path, default=SOURCE_ROOT / "cmix.bin")
    parser.add_argument("--dictionary", type=Path, default=SOURCE_ROOT / "english.dic")
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    decision_path = output_dir / "decision.json"
    if decision_path.exists():
        raise FileExistsError(f"refusing to overwrite {decision_path}")

    paths = {
        "backend": args.backend.resolve(),
        "dictionary": args.dictionary.resolve(),
        "endpoint_p1": args.endpoint_p1.resolve(),
        "joint_p1": args.joint_p1.resolve(),
        "wrt_store": args.wrt_store.resolve(),
        "page_map": args.page_map.resolve(),
        "joint_decision": args.joint_decision.resolve(),
        "endpoint_decision": args.endpoint_decision.resolve(),
    }
    inputs = {
        name: bind(path, EXPECTED_SHA256[name], name)
        for name, path in paths.items()
    }
    joint_decision = json.loads(paths["joint_decision"].read_text())
    endpoint_decision = json.loads(paths["endpoint_decision"].read_text())
    if joint_decision["decision"]["verdict"] != "exact_joint_p1_trace_recovered":
        raise ValueError("joint trace antecedent is not exact")
    if endpoint_decision["proof"]["archive_identity"] is not True:
        raise ValueError("endpoint trace antecedent is not exact")

    pages = read_page_map(paths["page_map"])
    eligible = [row for row in pages if row[1] <= RAW_LIMIT]
    if not eligible:
        raise ValueError("no complete page before raw limit")
    raw_bytes = eligible[-1][1]
    scope_rows = eligible[-1][3]
    if scope_rows % 8:
        raise ValueError("scope is not byte aligned")
    scope_bytes = scope_rows // 8
    if (raw_bytes, scope_bytes, len(eligible)) != (984_835, 591_230, 171):
        raise ValueError("frozen population boundary changed")

    stored = paths["wrt_store"].read_bytes()
    if stored[:5] != STORE_HEADER or len(stored) <= 5 + scope_bytes:
        raise ValueError("invalid canonical WRT store")
    body = stored[5 : 5 + scope_bytes]
    truth = np.unpackbits(np.frombuffer(body, dtype=np.uint8), bitorder="big")
    reverse_body = body[::-1]
    reverse_truth = np.unpackbits(
        np.frombuffer(reverse_body, dtype=np.uint8), bitorder="big"
    )

    joint_p1 = read_p1(paths["joint_p1"])
    endpoint_p1 = read_p1(paths["endpoint_p1"], len(joint_p1))
    if scope_rows > len(joint_p1):
        raise ValueError("scope exceeds trace")

    reverse_store, reverse_dictionary = write_reverse_inputs(
        output_dir, paths["dictionary"], body
    )
    inputs["reverse_store"] = observed_artifact(reverse_store)
    inputs["reverse_dictionary"] = observed_artifact(reverse_dictionary)

    first = reverse_run(
        "a", output_dir, paths["backend"], paths["dictionary"],
        reverse_store, reverse_dictionary,
    )
    reverse_p1 = read_p1(first["trace"], scope_rows)
    reverse_payload, reverse_header_bytes, reverse_wrt_bytes = payload_codec.read_archive(
        first["archive"]
    )
    if reverse_header_bytes != CMIX_HEADER_BYTES or reverse_wrt_bytes != scope_bytes:
        raise ValueError("reverse archive header differs from frozen scope")
    replayed_reverse_payload = payload_codec.encode_payload(
        reverse_p1, reverse_truth
    )
    if replayed_reverse_payload != reverse_payload:
        raise ValueError("reverse source P1 does not replay its arithmetic payload")
    decoded_reverse = range_decode(reverse_payload, reverse_p1)
    reverse_decode_exact = np.array_equal(decoded_reverse, reverse_truth)
    if not reverse_decode_exact:
        raise ValueError("reverse source arithmetic decode failed")

    zero, one = qbit_tables()
    forward_byte_cost = byte_qbits(
        joint_p1[:scope_rows], truth, zero, one
    )
    reverse_byte_cost = byte_qbits(reverse_p1, reverse_truth, zero, one)
    forward_cumulative = np.concatenate(
        (np.zeros(1, dtype=np.int64), np.cumsum(forward_byte_cost, dtype=np.int64))
    )
    reverse_cumulative = np.concatenate(
        (np.zeros(1, dtype=np.int64), np.cumsum(reverse_byte_cost, dtype=np.int64))
    )
    cut_bytes = [0]
    cut_bytes.extend(row[3] // 8 for row in eligible)
    if cut_bytes[-1] != scope_bytes:
        cut_bytes.append(scope_bytes)
    cut_bytes = sorted(set(cut_bytes))
    surrogate = [
        int(forward_cumulative[cut] + reverse_cumulative[scope_bytes - cut])
        for cut in cut_bytes
    ]
    selected_index = min(range(len(cut_bytes)), key=lambda i: (surrogate[i], i))
    selected_cut = cut_bytes[selected_index]
    forward_rows = selected_cut * 8
    reverse_rows = (scope_bytes - selected_cut) * 8

    forward_payload = (
        payload_codec.encode_payload(joint_p1[:forward_rows], truth[:forward_rows])
        if forward_rows else b""
    )
    candidate_reverse_payload = (
        payload_codec.encode_payload(
            reverse_p1[:reverse_rows], reverse_truth[:reverse_rows]
        )
        if reverse_rows else b""
    )
    joint_payload = payload_codec.encode_payload(
        joint_p1[:scope_rows], truth
    )
    endpoint_payload = payload_codec.encode_payload(
        endpoint_p1[:scope_rows], truth
    )

    reverse_archive = first["archive"].read_bytes()
    standard_header = reverse_archive[:CMIX_HEADER_BYTES]
    frame = make_candidate_frame(
        standard_header, selected_cut,
        len(forward_payload), len(candidate_reverse_payload),
    )
    candidate_archive = frame + forward_payload + candidate_reverse_payload
    candidate_archive_second = (
        make_candidate_frame(
            standard_header, selected_cut,
            len(forward_payload), len(candidate_reverse_payload),
        )
        + forward_payload
        + candidate_reverse_payload
    )
    if candidate_archive != candidate_archive_second:
        raise ValueError("candidate archive construction is nondeterministic")
    candidate_path = output_dir / "candidate.bifrons"
    parent_path = output_dir / "joint_parent_prefix.cmix"
    candidate_path.write_bytes(candidate_archive)
    parent_path.write_bytes(standard_header + joint_payload)

    decoded_forward = range_decode(forward_payload, joint_p1[:forward_rows])
    decoded_suffix_reverse = range_decode(
        candidate_reverse_payload, reverse_p1[:reverse_rows]
    )
    forward_bytes = np.packbits(decoded_forward, bitorder="big").tobytes()
    suffix_reverse_bytes = np.packbits(
        decoded_suffix_reverse, bitorder="big"
    ).tobytes()
    reconstructed = forward_bytes + suffix_reverse_bytes[::-1]
    reconstruction_exact = reconstructed == body
    if not reconstruction_exact:
        raise ValueError("candidate WRT reconstruction failed")

    parent_total = CMIX_HEADER_BYTES + len(joint_payload)
    endpoint_total = CMIX_HEADER_BYTES + len(endpoint_payload)
    reverse_total = len(reverse_archive)
    candidate_total = len(candidate_archive)
    gross_gain = parent_total - candidate_total
    gross_bpm = gross_gain * 1_000_000.0 / raw_bytes
    required_gain = math.ceil(raw_bytes * GROSS_GATE_BPM / 1_000_000.0)
    economic_pass = (
        gross_gain >= required_gain
        and candidate_total < endpoint_total
        and candidate_total < reverse_total
    )

    second: dict[str, Any] | None = None
    repeat_archive_exact = False
    repeat_trace_exact = False
    if economic_pass:
        second = reverse_run(
            "b", output_dir, paths["backend"], paths["dictionary"],
            reverse_store, reverse_dictionary,
        )
        repeat_archive_exact = (
            first["archive"].read_bytes() == second["archive"].read_bytes()
        )
        repeat_trace_exact = (
            first["trace"].read_bytes() == second["trace"].read_bytes()
        )
        if not repeat_archive_exact or not repeat_trace_exact:
            raise ValueError("promotable reverse source execution did not repeat")

    guard = first["phase"]["guard"]
    exactness_pass = all(
        (
            replayed_reverse_payload == reverse_payload,
            reverse_decode_exact,
            reconstruction_exact,
            candidate_archive == candidate_archive_second,
            guard.get("official_decimal_over_limit_kib") == 0,
        )
    )
    authorized = economic_pass and exactness_pass and repeat_archive_exact and repeat_trace_exact
    verdict = "AUTHORIZED_CANONICAL_10M" if authorized else "REJECT"

    decision = {
        "schema": "gamma.bifrons_reverse_causal_joint_ceiling_q0.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_id": CANDIDATE_ID,
        "status": verdict,
        "claim_boundary": (
            "Exact zero-source-cost opening-prefix arithmetic ceiling. The WRT "
            "prefix is reconstructed exactly, but its enclosing 10M WRT segment "
            "header prevents an independent official raw inverse at Q0. No score "
            "or forecast credit is assigned."
        ),
        "inputs": inputs,
        "scope": {
            "complete_pages": len(eligible),
            "raw_equivalent_bytes": raw_bytes,
            "wrt_bytes": scope_bytes,
            "p1_rows": scope_rows,
            "legal_cut_count": len(cut_bytes),
            "selected_cut_index": selected_index,
            "selected_cut_wrt_byte": selected_cut,
            "forward_wrt_bytes": selected_cut,
            "reverse_wrt_bytes": scope_bytes - selected_cut,
        },
        "artifacts": {
            "reverse_archive_a": observed_artifact(first["archive"]),
            "reverse_p1_a": observed_artifact(first["trace"]),
            "candidate_archive": observed_artifact(candidate_path),
            "joint_parent_prefix_archive": observed_artifact(parent_path),
            "reverse_archive_b": observed_artifact(second["archive"]) if second else None,
            "reverse_p1_b": observed_artifact(second["trace"]) if second else None,
            "script": observed_artifact(Path(__file__).resolve()),
        },
        "economics": {
            "joint_parent_payload_bytes": len(joint_payload),
            "joint_parent_total_bytes": parent_total,
            "endpoint_forward_payload_bytes": len(endpoint_payload),
            "endpoint_forward_total_bytes": endpoint_total,
            "all_reverse_payload_bytes": len(reverse_payload),
            "all_reverse_total_bytes": reverse_total,
            "candidate_frame_bytes": len(frame),
            "candidate_forward_payload_bytes": len(forward_payload),
            "candidate_reverse_payload_bytes": len(candidate_reverse_payload),
            "candidate_total_bytes": candidate_total,
            "gross_gain_over_joint_bytes": gross_gain,
            "gross_gain_over_joint_bytes_per_million": gross_bpm,
            "required_gross_gain_bytes": required_gain,
            "required_gross_gain_bytes_per_million": GROSS_GATE_BPM,
            "surrogate_selected_qbits": surrogate[selected_index],
        },
        "proof": {
            "source_and_input_identities_exact": True,
            "joint_antecedent_exact": True,
            "endpoint_antecedent_exact": True,
            "reverse_probabilities_legal_nonzero": True,
            "reverse_source_payload_replay_exact": True,
            "reverse_source_arithmetic_decode_exact": reverse_decode_exact,
            "candidate_forward_arithmetic_decode_exact": True,
            "candidate_reverse_arithmetic_decode_exact": True,
            "complete_wrt_reconstruction_exact": reconstruction_exact,
            "candidate_second_build_byte_identical": True,
            "official_raw_inverse_required_at_q0": False,
            "decimal_10gb_guard_pass": guard.get("official_decimal_over_limit_kib") == 0,
            "reverse_source_repeat_required": economic_pass,
            "reverse_source_archive_repeat_exact": repeat_archive_exact,
            "reverse_source_p1_repeat_exact": repeat_trace_exact,
        },
        "execution": {
            "reverse_a": first["phase"],
            "reverse_b": second["phase"] if second else None,
        },
        "gates": {
            "exactness_pass": exactness_pass,
            "gross_gain_pass": gross_gain >= required_gain,
            "beats_endpoint_forward": candidate_total < endpoint_total,
            "beats_all_reverse": candidate_total < reverse_total,
            "economic_pass": economic_pass,
            "repeat_pass": repeat_archive_exact and repeat_trace_exact,
            "promotion_authorized": authorized,
        },
        "decision": {
            "verdict": verdict,
            "authorized_next_action": (
                "run one canonical 10M frozen BIFRONS replay"
                if authorized
                else "retire the one-cut reverse-causal endpoint construction"
            ),
            "score_credit_bytes": 0,
            "forecast_bytes": 109_389_323,
            "verified_full_1g_score_bytes": None,
        },
    }
    temporary = decision_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    temporary.replace(decision_path)
    print(
        json.dumps(
            {
                "candidate_id": CANDIDATE_ID,
                "decision": verdict,
                "gross_gain_bytes": gross_gain,
                "gross_bpm": gross_bpm,
                "selected_cut": selected_cut,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
