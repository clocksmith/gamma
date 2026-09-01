#!/usr/bin/env python3
"""Run the corrected bounded Endpoint428 Fiber-FOSSIL v4 finite-coder gate."""

from __future__ import annotations

from array import array
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "wiki_fiber_fossil_endpoint428_opening1m_q0_v4"
RESULT = PROJECT / "results" / CANDIDATE_ID
EXPERIMENT = PROJECT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
SEMANTIC_REVISION = PROJECT / "operations/adaptive/candidate-revisions/endpoint428_semantic_route_tape_q0_v3/20260901T131904564070Z_c0f355845c3b.json"
SEMANTIC_SCANNER = PROJECT / "operations/adaptive/candidate-blobs/sha256/b4/b44fffb2b95c540535d293e1d0021f544a5b7e4d8fbb740721752a69b0c7866e"
PARENT_RECEIPT = PROJECT / "results/endpoint428_pair_layer0_online_native_1m_v1/receipt.json"
WRT_STORE = Path("/home/x/enwiki9-nonproof/results/fx2_wrt_store_1m.bin")
RAW = PROJECT / "data/enwik9_1000000.bin"
DICTIONARY = Path("/home/x/enwiki9-nonproof/cmix21-lstm200-plus-fx2lite428-onlinepairlayer0-v17/english.dic")
P1 = Path("/home/x/enwiki9-nonproof/results/endpoint428_pair_layer0_online_native_1m_v1/native.p1")
PARENT_ARCHIVE = Path("/home/x/enwiki9-nonproof/results/endpoint428_pair_layer0_online_native_1m_v1/archive.bin")
COMPILER = Path("/usr/bin/x86_64-linux-gnu-g++-15")

EXPECTED = {
    # The adaptive queue binds the frozen experiment digest to this runner.
    # Keeping that binding outside this file avoids a runner/contract digest
    # cycle while the runner still records the exact experiment artifact.
    "experiment": (None, None),
    "semantic_revision": (None, "031036a3f62bee9adaab1a88c2070ea71c66c8bc900b67e2b1b033f338d0bb58"),
    "semantic_scanner": (32781, "b44fffb2b95c540535d293e1d0021f544a5b7e4d8fbb740721752a69b0c7866e"),
    "parent_receipt": (None, "e19401d0c592c2bc81a558db4a625c027d35688ea3b257cc31f6f27e109b86ae"),
    "wrt_store": (600747, "1e209c7d19a22af5ce6a1de3bab1fc636669f40686aebd88bbe9dc8e5411e583"),
    "raw": (1000000, "369b688978f649681136198fb96db14c1616756260c55fb4b65e9bc049552cad"),
    "dictionary": (411996, "4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a"),
    "p1": (9611888, "a37c80c4167ef0c26bc3b8884de93c0a12224e8113e00ad1e33bfaf3fad1b898"),
    "parent_archive": (173896, "f167fe031ab00e012420c45ae283f90eeedec3c19462a47c29a27f99edbe4e29"),
    "candidate_program": (18563, "4fd89c60a726c754bfd49967e02ddb811a74075c16f93783dbe78283ba537a22"),
}
FLAGS = [
    "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-pedantic",
    "-fno-fast-math", "-ffp-contract=off", "-march=x86-64", "-mtune=generic",
    "-Wl,--build-id=none",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def require_artifact(path: Path, expected: tuple[int | None, str | None],
                     label: str) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"missing {label}: {path}")
    row = artifact(path)
    if ((expected[0] is not None and row["bytes"] != expected[0])
            or (expected[1] is not None and row["sha256"] != expected[1])):
        raise RuntimeError(f"{label} identity mismatch: {row}")
    return row


def write_bytes(path: Path, data: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def run_logged(command: list[str], log: Path) -> None:
    with log.open("xb") as output:
        completed = subprocess.run(
            command, cwd=PROJECT, stdout=output,
            stderr=subprocess.STDOUT, check=False,
        )
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed returncode={completed.returncode}: {command}"
        )


def load_candidate_module() -> tuple[Any, Path]:
    root_text = os.environ.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT")
    if not root_text:
        raise RuntimeError("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT is required")
    root = Path(root_text).resolve()
    program = root / "program.py"
    interface = root / "interface-contract.json"
    if not program.is_file() or not interface.is_file():
        raise RuntimeError("adaptive candidate snapshot is incomplete")
    spec = importlib.util.spec_from_file_location("_fiber_fossil_gate", program)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load candidate snapshot")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, interface


def arm_probabilities(core: Any, arm: str, base: array,
                      candidates: dict[str, array]) -> array:
    return base if arm in ("P", "K") else candidates[arm]


def exact_evaluation(core: Any, stream: bytes, base: array,
                     candidates: dict[str, array], distances: list[int]
                     ) -> tuple[dict[str, bytes], dict[str, Any]]:
    truth = core.truth_bits(stream)
    arms = ("P", "K", "D", "G", "S", "R", "N", "T")
    payloads: dict[str, bytes] = {}
    inverse: dict[str, bool] = {}
    for arm in arms:
        probabilities = arm_probabilities(core, arm, base, candidates)
        payload = core.range_encode(probabilities, truth)
        payloads[arm] = payload
        inverse[arm] = core.range_decode_equal(payload, probabilities, truth)

    payload_bytes = {arm: len(payload) for arm, payload in payloads.items()}
    gains = {
        arm: payload_bytes["P"] - size for arm, size in payload_bytes.items()
    }
    boundaries = (0, len(truth) // 3, 2 * len(truth) // 3, len(truth))
    thirds: list[dict[str, Any]] = []
    for third in range(3):
        start, end = boundaries[third], boundaries[third + 1]
        third_truth = truth[start:end]
        sizes: dict[str, int] = {}
        for arm in arms:
            probabilities = arm_probabilities(core, arm, base, candidates)
            sizes[arm] = len(
                core.range_encode(probabilities[start:end], third_truth)
            )
        third_gains = {
            arm: sizes["P"] - size for arm, size in sizes.items()
        }
        thirds.append({
            "third": third,
            "start_row": start,
            "end_row": end,
            "payload_bytes": sizes,
            "gain_vs_parent_bytes": third_gains,
            "d_control_margin_bytes": (
                third_gains["D"]
                - max(third_gains[arm] for arm in core.CONTROLS)
            ),
        })

    distance_rows: list[dict[str, Any]] = []
    positive_buckets = 0
    for lower, upper in core.VIRTUAL_DISTANCE_BUCKETS:
        bucket = array("H", base)
        event_count = 0
        for source, distance in enumerate(distances):
            if lower <= distance <= upper:
                row = source * 8
                bucket[row : row + 8] = candidates["D"][row : row + 8]
                event_count += 1
        bucket_payload_bytes = len(core.range_encode(bucket, truth))
        gain = len(payloads["P"]) - bucket_payload_bytes
        if gain > 0:
            positive_buckets += 1
        distance_rows.append({
            "minimum_inclusive": lower,
            "maximum_inclusive": upper,
            "events": event_count,
            "payload_bytes": bucket_payload_bytes,
            "gain_vs_parent_bytes": gain,
        })

    evaluation = {
        "payload_bytes": payload_bytes,
        "gain_vs_parent_bytes": gains,
        "payload_sha256": {
            arm: hashlib.sha256(payload).hexdigest()
            for arm, payload in payloads.items()
        },
        "inverse_pass": inverse,
        "thirds": thirds,
        "virtual_distance_buckets": distance_rows,
        "positive_virtual_distance_bucket_count": positive_buckets,
        "d_minimum_control_margin_bytes": (
            gains["D"] - max(gains[arm] for arm in core.CONTROLS)
        ),
        "minimum_third_d_bytes_saved": min(
            row["gain_vs_parent_bytes"]["D"] for row in thirds
        ),
        "minimum_third_d_control_margin_bytes": min(
            row["d_control_margin_bytes"] for row in thirds
        ),
    }
    return payloads, evaluation


def main() -> int:
    core, interface = load_candidate_module()
    if not RESULT.is_dir() or any(RESULT.iterdir()):
        raise RuntimeError(
            f"result directory must be precreated and empty: {RESULT}"
        )
    inputs = {
        "experiment": require_artifact(
            EXPERIMENT, EXPECTED["experiment"], "experiment"
        ),
        "semantic_revision": require_artifact(
            SEMANTIC_REVISION, EXPECTED["semantic_revision"],
            "semantic revision",
        ),
        "semantic_scanner": require_artifact(
            SEMANTIC_SCANNER, EXPECTED["semantic_scanner"],
            "semantic scanner",
        ),
        "parent_receipt": require_artifact(
            PARENT_RECEIPT, EXPECTED["parent_receipt"], "parent receipt"
        ),
        "wrt_store": require_artifact(
            WRT_STORE, EXPECTED["wrt_store"], "WRT store"
        ),
        "raw": require_artifact(RAW, EXPECTED["raw"], "raw prefix"),
        "dictionary": require_artifact(
            DICTIONARY, EXPECTED["dictionary"], "dictionary"
        ),
        "p1": require_artifact(P1, EXPECTED["p1"], "parent P1"),
        "parent_archive": require_artifact(
            PARENT_ARCHIVE, EXPECTED["parent_archive"], "parent archive"
        ),
        "candidate_program": require_artifact(
            Path(core.__file__), EXPECTED["candidate_program"],
            "candidate program",
        ),
        "candidate_interface": artifact(interface),
        "compiler": artifact(COMPILER),
    }
    store_data = WRT_STORE.read_bytes()
    if store_data[:5] != b"\x80\0\0\0\0":
        raise RuntimeError("WRT wrapper mismatch")
    stream = store_data[5:]
    if len(stream) != 600742:
        raise RuntimeError("WRT stream length mismatch")

    with tempfile.TemporaryDirectory(
        prefix="gamma-fiber-fossil-build-"
    ) as temporary:
        binary = Path(temporary) / "semantic-route-tape"
        run_logged(
            [str(COMPILER), *FLAGS, "-x", "c++", str(SEMANTIC_SCANNER),
             "-o", str(binary)],
            RESULT / "compile.log",
        )
        write_json(RESULT / "build.json", {
            "schema": "gamma.enwiki9.wiki-fiber-fossil-build.v1",
            "candidate_id": CANDIDATE_ID,
            "inputs": inputs,
            "compiler_flags": FLAGS,
            "scanner_binary": artifact(binary),
            "archive_authority": False,
            "score_credit_bytes": 0,
        })
        for arm in ("a", "b"):
            run_logged([
                str(binary), str(WRT_STORE), str(RAW), str(DICTIONARY),
                str(RESULT / f"route-tape-{arm}.bin"),
                str(RESULT / f"route-descriptors-{arm}.bin"),
                str(RESULT / f"route-summary-{arm}.json"), "--fixture",
            ], RESULT / f"route-scan-{arm}.log")

    repeat_route_identity = all(
        sha256(RESULT / f"route-{kind}-a.{suffix}")
        == sha256(RESULT / f"route-{kind}-b.{suffix}")
        for kind, suffix in (
            ("tape", "bin"),
            ("descriptors", "bin"),
            ("summary", "json"),
        )
    )
    if not repeat_route_identity:
        raise RuntimeError("semantic route A/B identity mismatch")
    tape_data = (RESULT / "route-tape-a.bin").read_bytes()
    tape_header, tape_rows = core.load_tape(
        tape_data, 600747, 600742, 1000000, 411996
    )
    base = core.load_p1(P1.read_bytes(), len(stream) * 8)
    first, first_meta, first_distances = core.construct_probabilities(
        stream, base, tape_rows
    )
    first_digests = core.probability_digests(first)
    second, second_meta, second_distances = core.construct_probabilities(
        stream, base, tape_rows
    )
    second_digests = core.probability_digests(second)
    probability_repeat = (
        first_digests == second_digests
        and first_meta == second_meta
        and first_distances == second_distances
    )
    if not probability_repeat:
        raise RuntimeError("probability construction replay mismatch")
    del second, second_distances

    payloads, exact = exact_evaluation(
        core, stream, base, first, first_distances
    )
    for arm, payload in payloads.items():
        write_bytes(RESULT / f"payload-{arm}.bin", payload)
    parent_archive = PARENT_ARCHIVE.read_bytes()
    parent_payload_identity = parent_archive[37:] == payloads["P"]
    maximum_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    measurements = {
        "rawInversePass": (
            tape_header["raw_bytes"] == 1000000
            and tape_header["pretruth_violations"] == 0
        ),
        "parentPayloadIdentityPass": (
            parent_payload_identity and payloads["K"] == payloads["P"]
        ),
        "allCandidateInversePass": all(exact["inverse_pass"].values()),
        "repeatIdentityPass": repeat_route_identity and probability_repeat,
        "dPayloadBytesSaved": exact["gain_vs_parent_bytes"]["D"],
        "dMinimumControlMarginBytes": exact["d_minimum_control_margin_bytes"],
        "minimumThirdDBytesSaved": exact["minimum_third_d_bytes_saved"],
        "minimumThirdDControlMarginBytes": exact[
            "minimum_third_d_control_margin_bytes"
        ],
        "positiveVirtualDistanceBucketCount": exact[
            "positive_virtual_distance_bucket_count"
        ],
        "maximumProcessRssKiB": maximum_rss,
    }
    promotion = (
        measurements["rawInversePass"]
        and measurements["parentPayloadIdentityPass"]
        and measurements["allCandidateInversePass"]
        and measurements["repeatIdentityPass"]
        and measurements["dPayloadBytesSaved"] >= 4080
        and measurements["dMinimumControlMarginBytes"] > 0
        and measurements["minimumThirdDBytesSaved"] > 0
        and measurements["minimumThirdDControlMarginBytes"] > 0
        and measurements["positiveVirtualDistanceBucketCount"] >= 2
        and measurements["maximumProcessRssKiB"] <= 524288
    )
    receipt = {
        "schema": "gamma.enwiki9.wiki-fiber-fossil-endpoint428-opening1m.v1",
        "candidate_id": CANDIDATE_ID,
        "evidence_class": "causal_shadow",
        "inputs": inputs,
        "scope": {
            "raw_bytes": 1000000,
            "wrt_stream_bytes": len(stream),
            "rows": len(stream) * 8,
        },
        "semantic_route": {
            "header": tape_header,
            "records": len(tape_rows),
            "tape_a": artifact(RESULT / "route-tape-a.bin"),
            "tape_b": artifact(RESULT / "route-tape-b.bin"),
            "repeat_identity": repeat_route_identity,
        },
        "probability_replay": {
            "digests": first_digests,
            "repeat_identity": probability_repeat,
            "measurements": first_meta,
        },
        "exact_finite_arithmetic": exact,
        "measurements": measurements,
        "promotion_pass": promotion,
        "archive_authority": False,
        "native_integration_authority": False,
        "score_credit_bytes": 0,
        "claim_boundary": (
            "Bounded offline causal-shadow gate over immutable opening-1M "
            "evidence. No active HORIZON trace, full stream, submitted codec "
            "input, archive score, or objective credit is involved."
        ),
    }
    write_json(RESULT / "receipt.json", receipt)
    write_json(RESULT / "decision.json", {
        "schema": (
            "gamma.enwiki9.wiki-fiber-fossil-endpoint428-"
            "opening1m-decision.v1"
        ),
        "candidate_id": CANDIDATE_ID,
        "status": "passed" if promotion else "failed",
        "measurements": measurements,
        "receipt": artifact(RESULT / "receipt.json"),
        "next_action": (
            "authorize only one separately frozen native Fiber-FOSSIL P/K/D gate"
            if promotion
            else "retire semantic-distance exact retrieval before LOOM or route fast weights"
        ),
        "archive_authority": False,
        "score_credit_bytes": 0,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
