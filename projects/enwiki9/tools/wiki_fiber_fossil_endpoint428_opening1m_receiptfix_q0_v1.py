#!/usr/bin/env python3
"""Run Fiber-FOSSIL receiptfix-v1 through an outer-owned hard execution envelope."""

from __future__ import annotations

import argparse
from array import array
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import secrets
import signal
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "wiki_fiber_fossil_endpoint428_opening1m_receiptfix_q0_v1"
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
HARD_MEMORY_LIMIT_KIB = 524288
HARD_MEMORY_LIMIT_BYTES = HARD_MEMORY_LIMIT_KIB * 1024
CORE_SHA256 = "4fd89c60a726c754bfd49967e02ddb811a74075c16f93783dbe78283ba537a22"
HORIZON_RESULT_ROOTS = (
    (PROJECT / "results").resolve(),
    Path("/home/x/enwiki9-nonproof/results").resolve(),
)
PROCESS_TREE_PEAK_RSS_KIB = 0
HORIZON_DENIAL_COUNT = 0
DELEGATED_CGROUP_PARENT = Path(
    "/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice"
)
DELEGATED_CGROUP_PARENT_INODE = 8608
DELEGATED_CGROUP_PARENT_UID = 1000
DELEGATED_CGROUP_PARENT_GID = 1000
OWNED_CGROUP_PREFIX = "gamma-fiber-fossil-receiptfix-v1-"
OWNED_CGROUP_ENV = "GAMMA_FIBER_RECEIPTFIX_V1_OWNED_CGROUP_JSON"
PROVISIONAL_RECEIPT = "worker-receipt.provisional.json"
HORIZON_PROBE = "source-access-denial-probe.json"
FINAL_RECEIPT = "receipt.json"
FINAL_DECISION = "decision.json"
PAYLOAD_NAMES = tuple(f"payload-{arm}.bin" for arm in ("P", "K", "D", "G", "S", "R", "N", "T"))
DECLARED_OUTPUT_NAMES = frozenset({
    "compile.log",
    "build.json",
    "route-scan-a.log",
    "route-scan-b.log",
    "route-tape-a.bin",
    "route-tape-b.bin",
    "route-descriptors-a.bin",
    "route-descriptors-b.bin",
    "route-summary-a.json",
    "route-summary-b.json",
    *PAYLOAD_NAMES,
    HORIZON_PROBE,
    PROVISIONAL_RECEIPT,
    FINAL_RECEIPT,
    FINAL_DECISION,
})

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


def _is_horizon_artifact(path: Path) -> bool:
    resolved = path.resolve(strict=False)
    for root in HORIZON_RESULT_ROOTS:
        try:
            relative = resolved.relative_to(root)
        except ValueError:
            continue
        if any("horizon" in part.casefold() for part in relative.parts):
            return True
    return False


def install_horizon_access_guard() -> None:
    """Deny Python-side access to every HORIZON-named result subtree."""
    def audit(event: str, arguments: tuple[Any, ...]) -> None:
        global HORIZON_DENIAL_COUNT
        if event != "open" or not arguments:
            return
        target = arguments[0]
        if isinstance(target, int):
            return
        try:
            path = Path(os.fsdecode(target))
        except (TypeError, ValueError):
            return
        if _is_horizon_artifact(path):
            HORIZON_DENIAL_COUNT += 1
            raise PermissionError(f"active HORIZON artifacts are forbidden: {path}")

    sys.addaudithook(audit)


def apply_hard_rlimit() -> dict[str, int]:
    """Install a non-raising address-space ceiling inherited by descendants."""
    current_soft, current_hard = resource.getrlimit(resource.RLIMIT_AS)
    infinity = resource.RLIM_INFINITY
    effective = HARD_MEMORY_LIMIT_BYTES
    if current_hard != infinity:
        effective = min(effective, current_hard)
    if effective <= 0:
        raise RuntimeError("RLIMIT_AS has no positive enforceable range")
    resource.setrlimit(resource.RLIMIT_AS, (effective, effective))
    observed_soft, observed_hard = resource.getrlimit(resource.RLIMIT_AS)
    if observed_soft != effective or observed_hard != effective:
        raise RuntimeError("RLIMIT_AS did not bind to the requested hard ceiling")
    return {
        "requested_bytes": HARD_MEMORY_LIMIT_BYTES,
        "effective_bytes": effective,
        "prior_soft_bytes": current_soft,
        "prior_hard_bytes": current_hard,
    }


def cgroup_memory_envelope(require_hard_cap: bool) -> dict[str, Any]:
    """Resolve the effective cgroup-v2 cap; normal mode fails closed without it."""
    cgroup_line = None
    for line in Path("/proc/self/cgroup").read_text().splitlines():
        if line.startswith("0::"):
            cgroup_line = line[3:]
            break
    if cgroup_line is None:
        raise RuntimeError("unified cgroup-v2 membership is required")
    root = Path("/sys/fs/cgroup")
    current = (root / cgroup_line.lstrip("/")).resolve()
    if root.resolve() not in (current, *current.parents):
        raise RuntimeError("cgroup-v2 membership escaped the controller root")
    finite_caps: list[tuple[str, int]] = []
    cursor = current
    while True:
        maximum = cursor / "memory.max"
        if maximum.is_file():
            value = maximum.read_text().strip()
            if value != "max":
                finite_caps.append((str(maximum), int(value)))
        if cursor == root:
            break
        cursor = cursor.parent
    effective = min((value for _, value in finite_caps), default=None)
    admitted = effective is not None and effective <= HARD_MEMORY_LIMIT_BYTES
    result: dict[str, Any] = {
        "cgroup_path": str(current),
        "finite_ancestor_caps": finite_caps,
        "effective_memory_max_bytes": effective,
        "normal_execution_admitted": admitted,
    }
    if require_hard_cap and not admitted:
        raise RuntimeError(
            "normal receiptfix-v1 execution requires an effective cgroup-v2 memory.max "
            f"at or below {HARD_MEMORY_LIMIT_BYTES} bytes before corpus access"
        )
    return result


def owned_cgroup_binding() -> dict[str, Any]:
    encoded = os.environ.get(OWNED_CGROUP_ENV)
    if not encoded:
        raise RuntimeError("guarded receiptfix-v1 worker lacks owned cgroup binding")
    binding = json.loads(encoded)
    child = Path(binding["path"])
    if (
        child.parent != DELEGATED_CGROUP_PARENT
        or not valid_owned_cgroup_name(child.name)
        or child.stat().st_ino != binding["inode"]
        or int((child / "memory.max").read_text()) != HARD_MEMORY_LIMIT_BYTES
        or (child / "memory.swap.max").read_text().strip() != "0"
    ):
        raise RuntimeError("guarded receiptfix-v1 worker owned cgroup binding mismatch")
    current = cgroup_memory_envelope(True)
    if Path(current["cgroup_path"]) != child:
        raise RuntimeError("guarded receiptfix-v1 worker did not execute inside owned cgroup")
    return binding


def _children_of(pid: int) -> list[int]:
    task_root = Path("/proc") / str(pid) / "task"
    children: set[int] = set()
    try:
        tasks = list(task_root.iterdir())
    except OSError:
        return []
    for task in tasks:
        try:
            values = (task / "children").read_text().split()
        except OSError:
            continue
        for value in values:
            try:
                children.add(int(value))
            except ValueError:
                continue
    return sorted(children)


def _process_tree(root: int) -> list[int]:
    seen: set[int] = set()
    pending = [root]
    while pending:
        pid = pending.pop()
        if pid in seen:
            continue
        seen.add(pid)
        pending.extend(_children_of(pid))
    return sorted(seen)


def _rss_kib(pid: int) -> int:
    try:
        lines = (Path("/proc") / str(pid) / "status").read_text().splitlines()
    except OSError:
        return 0
    for line in lines:
        if line.startswith("VmRSS:"):
            fields = line.split()
            return int(fields[1]) if len(fields) >= 2 else 0
    return 0


def sample_process_tree_rss_kib() -> int:
    global PROCESS_TREE_PEAK_RSS_KIB
    observed = sum(_rss_kib(pid) for pid in _process_tree(os.getpid()))
    PROCESS_TREE_PEAK_RSS_KIB = max(PROCESS_TREE_PEAK_RSS_KIB, observed)
    return observed


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
    for argument in command:
        if _is_horizon_artifact(Path(argument)):
            raise PermissionError(
                f"subprocess HORIZON artifact access is forbidden: {argument}"
            )
    with log.open("xb") as output:
        process = subprocess.Popen(
            command, cwd=PROJECT, stdout=output,
            stderr=subprocess.STDOUT, start_new_session=True,
        )
        while process.poll() is None:
            observed = sample_process_tree_rss_kib()
            if observed > HARD_MEMORY_LIMIT_KIB:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                raise MemoryError(
                    "hard aggregate process-tree RSS ceiling exceeded: "
                    f"{observed} > {HARD_MEMORY_LIMIT_KIB} KiB"
                )
            time.sleep(0.01)
        returncode = process.returncode
    if returncode != 0:
        raise RuntimeError(
            f"command failed returncode={returncode}: {command}"
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


def _snapshot_root(argument: Path | None) -> Path:
    if argument is not None:
        return argument.resolve()
    root_text = os.environ.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT")
    if not root_text:
        raise RuntimeError("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT is required")
    return Path(root_text).resolve()


def validate_only(snapshot_root: Path, memory_envelope: dict[str, Any]) -> dict[str, Any]:
    program = snapshot_root / "program.py"
    interface_path = snapshot_root / "interface-contract.json"
    if sha256(program) != CORE_SHA256:
        raise RuntimeError("receiptfix-v1 must preserve the exact v4 algorithm bytes")
    interface = json.loads(interface_path.read_text())
    if interface.get("candidate_id") != CANDIDATE_ID:
        raise RuntimeError("receiptfix-v1 interface candidate identity mismatch")
    implementation = interface.get("bound_implementation", {})
    runner_digest = sha256(Path(__file__).resolve())
    if implementation != {
        "core": f"programs/{CANDIDATE_ID}/program.py",
        "core_sha256": CORE_SHA256,
        "runner": f"tools/{CANDIDATE_ID}.py",
        "runner_sha256": runner_digest,
    }:
        raise RuntimeError("receiptfix-v1 interface implementation binding mismatch")

    experiment = json.loads(EXPERIMENT.read_text())
    parent_experiment = json.loads(
        (PROJECT / "operations/adaptive/experiments/"
         "wiki_fiber_fossil_endpoint428_opening1m_q0_v4.json").read_text()
    )
    if experiment.get("controls") != parent_experiment.get("controls"):
        raise RuntimeError("receiptfix-v1 controls drifted from v4")
    if experiment.get("hypothesis") != parent_experiment.get("hypothesis"):
        raise RuntimeError("receiptfix-v1 scientific hypothesis drifted from v4")
    runner_inputs = [
        row for row in experiment.get("inputs", []) if row.get("id") == "runner"
    ]
    expected_runner = {
        "id": "runner",
        "path": f"tools/{CANDIDATE_ID}.py",
        "sha256": f"sha256:{runner_digest}",
    }
    if runner_inputs != [expected_runner]:
        raise RuntimeError("receiptfix-v1 experiment runner binding mismatch")
    expected_outputs = {
        f"results/{CANDIDATE_ID}/{name}" for name in DECLARED_OUTPUT_NAMES
    }
    observed_outputs = experiment.get("outputs", [])
    if len(observed_outputs) != len(set(observed_outputs)) or set(
        observed_outputs
    ) != expected_outputs:
        raise RuntimeError("receiptfix-v1 experiment output manifest is not exact and complete")

    denial_pass = False
    try:
        (PROJECT / "results/active-horizon-validation-probe/trace.bin").open("rb")
    except PermissionError:
        denial_pass = True
    if not denial_pass:
        raise RuntimeError("HORIZON access guard did not fail closed")
    return {
        "schema": "gamma.enwiki9.wiki-fiber-fossil-receiptfix-v1-validation.v1",
        "candidate_id": CANDIDATE_ID,
        "validation_only": True,
        "corpus_accessed": False,
        "algorithm_sha256": CORE_SHA256,
        "runner_sha256": runner_digest,
        "controls_identical_to_v4": True,
        "hypothesis_identical_to_v4": True,
        "hard_rlimit_as": memory_envelope,
        "horizon_artifact_access_denied": denial_pass,
        "declared_output_names": sorted(DECLARED_OUTPUT_NAMES),
        "compile_and_route_logs_declared": all(
            name in DECLARED_OUTPUT_NAMES for name in (
                "compile.log", "route-scan-a.log", "route-scan-b.log"
            )
        ),
        "worker_receipt_provisional_only": True,
        "outer_authoritative_finalizer": True,
    }


def perform_guarded_horizon_probe() -> dict[str, Any]:
    if not RESULT.is_dir() or any(RESULT.iterdir()):
        raise RuntimeError(
            f"result directory must be precreated and empty before probe: {RESULT}"
        )
    probe_path = (
        PROJECT / "results/active-horizon-receiptfix-v1-synthetic-probe/trace.bin"
    )
    denial_before = HORIZON_DENIAL_COUNT
    denial_error = None
    try:
        probe_path.open("rb")
    except PermissionError as error:
        denial_error = str(error)
    if denial_error is None or HORIZON_DENIAL_COUNT != denial_before + 1:
        raise RuntimeError("guarded worker HORIZON probe did not fail closed")
    probe = {
        "schema": "gamma.enwiki9.fiber-receiptfix-v1-horizon-denial-probe.v1",
        "candidate_id": CANDIDATE_ID,
        "synthetic_probe_path": str(probe_path),
        "attempted_operation": "python-open-read-binary",
        "denied_before_corpus": True,
        "denial_error": denial_error,
        "active_horizon_artifact_accessed": False,
        "corpus_accessed": False,
        "cgroup": owned_cgroup_binding(),
    }
    write_json(RESULT / HORIZON_PROBE, probe)
    return probe


def run_gate(memory_envelope: dict[str, Any], horizon_probe: dict[str, Any]) -> int:
    core, interface = load_candidate_module()
    if not RESULT.is_dir() or {path.name for path in RESULT.iterdir()} != {
        HORIZON_PROBE
    }:
        raise RuntimeError(
            "guarded worker requires exactly the pre-corpus HORIZON probe "
            f"artifact in {RESULT}"
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
    sample_process_tree_rss_kib()
    maximum_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    owned_binding = owned_cgroup_binding()
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
        "hardMemoryEnvelopePass": (
            memory_envelope["effective_bytes"] <= HARD_MEMORY_LIMIT_BYTES
            and memory_envelope["cgroup"]["normal_execution_admitted"]
            and PROCESS_TREE_PEAK_RSS_KIB <= HARD_MEMORY_LIMIT_KIB
        ),
        "activeHorizonAccessDeniedPass": (
            horizon_probe.get("denied_before_corpus") is True
            and horizon_probe.get("active_horizon_artifact_accessed") is False
        ),
        "ownedCgroupLifecyclePass": False,
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
        and measurements["hardMemoryEnvelopePass"]
        and measurements["activeHorizonAccessDeniedPass"]
    )
    receipt = {
        "schema": (
            "gamma.enwiki9.wiki-fiber-fossil-endpoint428-"
            "opening1m-worker-provisional.v1"
        ),
        "candidate_id": CANDIDATE_ID,
        "provisional_only": True,
        "authoritative": False,
        "outer_finalization_required": True,
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
        "horizon_denial_probe": horizon_probe,
        "execution_envelope": {
            "hard_rlimit_as": memory_envelope,
            "process_tree_peak_rss_kib": PROCESS_TREE_PEAK_RSS_KIB,
            "process_tree_rss_abort_kib": HARD_MEMORY_LIMIT_KIB,
            "sampling_interval_seconds": 0.01,
            "rlimit_inherited_by_descendants": True,
            "horizon_named_result_roots_denied": [
                str(path) for path in HORIZON_RESULT_ROOTS
            ],
            "owned_cgroup": owned_binding,
            "cleanup_authority": (
                "outer launcher makes job success conditional on removing only "
                "this verified empty owned inode"
            ),
        },
        "scientific_promotion_pass_provisional": promotion,
        "archive_authority": False,
        "native_integration_authority": False,
        "score_credit_bytes": 0,
        "claim_boundary": (
            "Bounded offline causal-shadow gate over immutable opening-1M "
            "evidence. No active HORIZON trace, full stream, submitted codec "
            "input, archive score, or objective credit is involved."
        ),
    }
    write_json(RESULT / PROVISIONAL_RECEIPT, receipt)
    return 0


def validate_delegated_cgroup_parent() -> dict[str, Any]:
    parent = DELEGATED_CGROUP_PARENT.resolve()
    if parent != DELEGATED_CGROUP_PARENT:
        raise RuntimeError("delegated cgroup parent path is not canonical")
    info = parent.stat()
    expected = (
        DELEGATED_CGROUP_PARENT_INODE,
        DELEGATED_CGROUP_PARENT_UID,
        DELEGATED_CGROUP_PARENT_GID,
    )
    observed = (info.st_ino, info.st_uid, info.st_gid)
    if observed != expected:
        raise RuntimeError(
            f"delegated cgroup parent identity mismatch: {observed} != {expected}"
        )
    if (parent / "cgroup.type").read_text().strip() != "domain":
        raise RuntimeError("delegated cgroup parent is not a domain cgroup")
    controllers = set((parent / "cgroup.controllers").read_text().split())
    subtree = set((parent / "cgroup.subtree_control").read_text().split())
    if "memory" not in controllers or "memory" not in subtree:
        raise RuntimeError("delegated cgroup parent lacks enabled memory controller")
    if (parent / "cgroup.procs").read_text().split():
        raise RuntimeError("delegated cgroup parent has direct process occupants")
    if not os.access(parent, os.W_OK):
        raise RuntimeError("delegated cgroup parent is not writable")
    return {
        "path": str(parent),
        "inode": info.st_ino,
        "uid": info.st_uid,
        "gid": info.st_gid,
        "memory_controller_enabled": True,
        "direct_processes_empty": True,
    }


def valid_owned_cgroup_name(name: str) -> bool:
    return re.fullmatch(
        re.escape(OWNED_CGROUP_PREFIX) + r"[0-9]+-[0-9a-f]{32}\.scope",
        name,
    ) is not None


def new_owned_cgroup_name() -> str:
    name = f"{OWNED_CGROUP_PREFIX}{os.getpid()}-{secrets.token_hex(16)}.scope"
    if not valid_owned_cgroup_name(name):
        raise RuntimeError("owned cgroup name lacks an exact 128-bit token")
    return name


def create_owned_cgroup(memory_max_bytes: int) -> tuple[Path, int]:
    validate_delegated_cgroup_parent()
    name = new_owned_cgroup_name()
    child = DELEGATED_CGROUP_PARENT / name
    child.mkdir(mode=0o755)
    child_inode = child.stat().st_ino
    try:
        if child.parent != DELEGATED_CGROUP_PARENT or not valid_owned_cgroup_name(
            name
        ):
            raise RuntimeError("owned cgroup path construction failed")
        (child / "memory.max").write_text(f"{memory_max_bytes}\n")
        if int((child / "memory.max").read_text()) != memory_max_bytes:
            raise RuntimeError("owned cgroup memory.max mismatch")
        swap_max = child / "memory.swap.max"
        if not swap_max.is_file():
            raise RuntimeError("owned cgroup lacks required memory.swap.max")
        swap_max.write_text("0\n")
        if swap_max.read_text().strip() != "0":
            raise RuntimeError("owned cgroup memory.swap.max mismatch")
        oom_group = child / "memory.oom.group"
        if oom_group.is_file():
            oom_group.write_text("1\n")
        peak = child / "memory.peak"
        if peak.is_file():
            peak.write_text("0\n")
        if (child / "cgroup.procs").read_text().split():
            raise RuntimeError("new owned cgroup is not empty")
        return child, child_inode
    except Exception:
        if child.is_dir() and not (child / "cgroup.procs").read_text().split():
            child.rmdir()
        raise


def read_cgroup_events(child: Path) -> dict[str, int]:
    events: dict[str, int] = {}
    for line in (child / "memory.events").read_text().splitlines():
        key, value = line.split()
        events[key] = int(value)
    return events


def remove_owned_empty_cgroup(child: Path, child_inode: int) -> dict[str, Any]:
    if (
        child.parent != DELEGATED_CGROUP_PARENT
        or not valid_owned_cgroup_name(child.name)
        or child.stat().st_ino != child_inode
    ):
        raise RuntimeError("refusing to remove an unowned cgroup")
    deadline = time.monotonic() + 5.0
    while (child / "cgroup.procs").read_text().split():
        if time.monotonic() >= deadline:
            kill = child / "cgroup.kill"
            if kill.is_file():
                kill.write_text("1\n")
                deadline = time.monotonic() + 5.0
            else:
                raise RuntimeError("owned cgroup remained occupied")
        time.sleep(0.01)
    empty_before_remove = not (child / "cgroup.procs").read_text().split()
    same_inode_before_remove = child.stat().st_ino == child_inode
    if not empty_before_remove or not same_inode_before_remove:
        raise RuntimeError("owned cgroup identity or emptiness drifted before cleanup")
    child.rmdir()
    if child.exists():
        raise RuntimeError("owned cgroup cleanup failed")
    residue = [
        path.name for path in DELEGATED_CGROUP_PARENT.iterdir()
        if path.name == child.name
    ]
    if residue:
        raise RuntimeError("owned cgroup residue remained after cleanup")
    return {
        "empty_before_remove": empty_before_remove,
        "same_inode_before_remove": same_inode_before_remove,
        "removed": True,
        "no_residue": True,
    }


def launch_in_owned_cgroup(
    command: list[str], memory_max_bytes: int, capture_output: bool,
) -> tuple[int, str, dict[str, Any]]:
    for argument in command:
        if _is_horizon_artifact(Path(argument)):
            raise PermissionError(f"HORIZON subprocess path denied: {argument}")
    child, child_inode = create_owned_cgroup(memory_max_bytes)
    wrapper = 'printf "%s\\n" "$$" > "$1/cgroup.procs" || exit 125; shift; exec "$@"'
    process: subprocess.Popen[str] | None = None
    peak_bytes = 0
    joined = False
    output = ""
    returncode: int | None = None
    events_before = read_cgroup_events(child)
    events_after = events_before
    cleanup: dict[str, Any] | None = None
    report: dict[str, Any] = {}
    try:
        environment = os.environ.copy()
        environment[OWNED_CGROUP_ENV] = json.dumps({
            "path": str(child),
            "inode": child_inode,
            "delegated_parent": str(DELEGATED_CGROUP_PARENT),
            "memory_max_bytes": memory_max_bytes,
            "cleanup_pending": True,
        }, sort_keys=True)
        process = subprocess.Popen(
            ["/bin/sh", "-c", wrapper, "fiber-receiptfix-v1", str(child), *command],
            cwd=PROJECT,
            env=environment,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.STDOUT if capture_output else None,
            text=True,
            start_new_session=True,
        )
        join_deadline = time.monotonic() + 5.0
        while time.monotonic() < join_deadline:
            pids = {int(value) for value in (child / "cgroup.procs").read_text().split()}
            if process.pid in pids:
                joined = True
                break
            if process.poll() is not None:
                break
            time.sleep(0.01)
        if not joined:
            raise RuntimeError("worker did not join owned cgroup before exec")
        while process.poll() is None:
            current = int((child / "memory.current").read_text())
            peak_bytes = max(peak_bytes, current)
            if current > memory_max_bytes:
                raise MemoryError("owned cgroup exceeded configured memory.max")
            time.sleep(0.01)
        if capture_output and process.stdout is not None:
            output = process.stdout.read()
        returncode = process.returncode
        peak_path = child / "memory.peak"
        if not peak_path.is_file():
            raise RuntimeError("owned cgroup lacks required memory.peak")
        peak_bytes = max(peak_bytes, int(peak_path.read_text()))
        events_after = read_cgroup_events(child)
        if int((child / "memory.max").read_text()) != memory_max_bytes:
            raise RuntimeError("owned cgroup memory.max drifted before cleanup")
        if (child / "memory.swap.max").read_text().strip() != "0":
            raise RuntimeError("owned cgroup memory.swap.max drifted before cleanup")
        report = {
            "delegated_parent": validate_delegated_cgroup_parent(),
            "owned_path": str(child),
            "owned_name": child.name,
            "owned_inode": child_inode,
            "owned_token_bits": 128,
            "memory_max_bytes": memory_max_bytes,
            "memory_swap_max_bytes": 0,
            "joined_before_exec": joined,
            "memory_peak_bytes": peak_bytes,
            "memory_events_before": events_before,
            "memory_events_after": events_after,
            "memory_events_delta": {
                key: events_after.get(key, 0) - events_before.get(key, 0)
                for key in sorted(set(events_before) | set(events_after))
            },
            "child_exit": {
                "returncode": returncode,
                "exited": returncode is not None,
                "success": returncode == 0,
            },
        }
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        cleanup = remove_owned_empty_cgroup(child, child_inode)
    if returncode is None or cleanup is None:
        raise RuntimeError("owned cgroup worker lacked terminal state")
    report["cleanup"] = cleanup
    report["authoritative_envelope_complete"] = all((
        report["joined_before_exec"],
        report["child_exit"]["exited"],
        cleanup["empty_before_remove"],
        cleanup["same_inode_before_remove"],
        cleanup["removed"],
        cleanup["no_residue"],
    ))
    return returncode, output, report


def require_exact_output_names(expected: frozenset[str]) -> dict[str, Any]:
    if not RESULT.is_dir():
        raise RuntimeError(f"missing candidate result directory: {RESULT}")
    entries = list(RESULT.iterdir())
    non_regular = sorted(
        path.name for path in entries if not path.is_file() or path.is_symlink()
    )
    observed = {path.name for path in entries}
    missing = sorted(expected - observed)
    extra = sorted(observed - expected)
    if non_regular or missing or extra:
        raise RuntimeError(
            "exact output manifest mismatch: "
            f"missing={missing} extra={extra} non_regular={non_regular}"
        )
    return {
        "declared_names": sorted(expected),
        "observed_names": sorted(observed),
        "missing": [],
        "extra": [],
        "non_regular": [],
        "exact_pass": True,
    }


def output_manifest_record(path: Path, declared_name: str | None = None) -> dict[str, Any]:
    name = path.name if declared_name is None else declared_name
    if name not in DECLARED_OUTPUT_NAMES or not path.is_file() or path.is_symlink():
        raise RuntimeError(f"cannot bind undeclared or non-regular output: {path}")
    return {
        "path": f"results/{CANDIDATE_ID}/{name}",
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def build_output_manifest(names: frozenset[str]) -> list[dict[str, Any]]:
    require_exact_output_names(names)
    return [output_manifest_record(RESULT / name) for name in sorted(names)]


def verify_output_manifest(
    manifest: list[dict[str, Any]], names: frozenset[str],
    present_names: frozenset[str] | None = None,
) -> None:
    expected_paths = {
        f"results/{CANDIDATE_ID}/{name}" for name in names
    }
    if (
        len(manifest) != len(names)
        or any(set(row) != {"path", "bytes", "sha256"} for row in manifest)
        or {row["path"] for row in manifest} != expected_paths
    ):
        raise RuntimeError("content manifest is not an exact-once path partition")
    require_exact_output_names(names if present_names is None else present_names)
    observed = [output_manifest_record(RESULT / name) for name in sorted(names)]
    if manifest != observed:
        raise RuntimeError("content manifest hash or size drift")


def write_staged_json(label: str, payload: dict[str, Any]) -> Path:
    token = secrets.token_hex(16)
    staged = RESULT.parent / f".{CANDIDATE_ID}.{label}.{token}.tmp"
    write_json(staged, payload)
    return staged


def publish_staged_file(staged: Path, destination: Path) -> None:
    if destination.exists() or destination.is_symlink():
        raise RuntimeError(f"refusing to replace canonical authority: {destination}")
    os.link(staged, destination, follow_symlinks=False)
    staged.unlink()
    directory_fd = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def rollback_authority_files() -> None:
    for name in (FINAL_DECISION, FINAL_RECEIPT):
        path = RESULT / name
        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.exists():
            raise RuntimeError(f"cannot roll back non-regular authority path: {path}")
    survivors = [
        name for name in (FINAL_DECISION, FINAL_RECEIPT)
        if (RESULT / name).exists() or (RESULT / name).is_symlink()
    ]
    if survivors:
        raise RuntimeError(f"authoritative artifacts survived rollback: {survivors}")


def finalize_authoritative_result(
    cgroup: dict[str, Any],
    failure_injector: Callable[[str], None] | None = None,
) -> None:
    pre_final_names = DECLARED_OUTPUT_NAMES - {FINAL_RECEIPT, FINAL_DECISION}
    pre_final_names = frozenset(pre_final_names)
    pre_final_manifest = build_output_manifest(pre_final_names)
    provisional_path = RESULT / PROVISIONAL_RECEIPT
    provisional = json.loads(provisional_path.read_text())
    if (
        provisional.get("candidate_id") != CANDIDATE_ID
        or provisional.get("provisional_only") is not True
        or provisional.get("authoritative") is not False
        or provisional.get("outer_finalization_required") is not True
    ):
        raise RuntimeError("invalid guarded-worker provisional receipt")
    probe_path = RESULT / HORIZON_PROBE
    probe = json.loads(probe_path.read_text())
    if (
        probe.get("candidate_id") != CANDIDATE_ID
        or probe.get("denied_before_corpus") is not True
        or probe.get("active_horizon_artifact_accessed") is not False
        or probe.get("corpus_accessed") is not False
    ):
        raise RuntimeError("invalid guarded-worker HORIZON probe evidence")
    worker_binding = provisional.get("execution_envelope", {}).get(
        "owned_cgroup", {}
    )
    expected_worker_binding = {
        "path": cgroup.get("owned_path"),
        "inode": cgroup.get("owned_inode"),
        "delegated_parent": str(DELEGATED_CGROUP_PARENT),
        "memory_max_bytes": HARD_MEMORY_LIMIT_BYTES,
        "cleanup_pending": True,
    }
    if worker_binding != expected_worker_binding or probe.get(
        "cgroup"
    ) != expected_worker_binding:
        raise RuntimeError("worker evidence does not bind the authoritative cgroup")
    events_delta = cgroup["memory_events_delta"]
    required_events = {"max", "oom", "oom_kill"}
    delegated = cgroup.get("delegated_parent", {})
    cgroup_pass = all((
        cgroup.get("owned_path") == str(
            DELEGATED_CGROUP_PARENT / cgroup.get("owned_name", "")
        ),
        valid_owned_cgroup_name(cgroup.get("owned_name", "")),
        cgroup.get("owned_token_bits") == 128,
        delegated.get("path") == str(DELEGATED_CGROUP_PARENT),
        delegated.get("inode") == DELEGATED_CGROUP_PARENT_INODE,
        delegated.get("uid") == DELEGATED_CGROUP_PARENT_UID,
        delegated.get("gid") == DELEGATED_CGROUP_PARENT_GID,
        cgroup["memory_max_bytes"] == HARD_MEMORY_LIMIT_BYTES,
        cgroup["memory_swap_max_bytes"] == 0,
        cgroup["joined_before_exec"],
        cgroup["memory_peak_bytes"] <= HARD_MEMORY_LIMIT_BYTES,
        required_events.issubset(cgroup["memory_events_before"]),
        required_events.issubset(cgroup["memory_events_after"]),
        all(value >= 0 for value in events_delta.values()),
        events_delta.get("max", 0) == 0,
        events_delta.get("oom", 0) == 0,
        events_delta.get("oom_kill", 0) == 0,
        cgroup["child_exit"]["success"],
        cgroup["cleanup"]["empty_before_remove"],
        cgroup["cleanup"]["same_inode_before_remove"],
        cgroup["cleanup"]["removed"],
        cgroup["cleanup"]["no_residue"],
        cgroup["authoritative_envelope_complete"],
    ))
    if not cgroup_pass:
        raise RuntimeError("authoritative cgroup envelope did not pass")
    receipt_measurements = dict(provisional["measurements"])
    receipt_measurements["hardMemoryEnvelopePass"] = True
    receipt_measurements["activeHorizonAccessDeniedPass"] = True
    receipt_measurements["ownedCgroupLifecyclePass"] = True
    receipt_measurements.pop("authoritativeOuterFinalizationPass", None)
    receipt_measurements.pop("completeOutputManifestPass", None)
    receipt = dict(provisional)
    receipt.update({
        "schema": (
            "gamma.enwiki9.wiki-fiber-fossil-endpoint428-"
            "opening1m-outer-receipt-pending-decision.v1"
        ),
        "provisional_only": False,
        "authoritative": False,
        "authority_requires_terminal_decision": True,
        "outer_finalization_required": True,
        "worker_provisional_receipt": artifact(provisional_path),
        "horizon_denial_probe": artifact(probe_path),
        "measurements": receipt_measurements,
        "authoritative_cgroup": cgroup,
        "pre_authority_content_manifest": {
            "policy": "exact-path-bytes-sha256-v1",
            "entries": pre_final_manifest,
            "exact_once_pass": True,
        },
    })
    receipt.pop("scientific_promotion_pass_provisional", None)
    receipt_stage: Path | None = None
    decision_stage: Path | None = None
    published = False
    try:
        receipt_stage = write_staged_json("receipt", receipt)
        receipt_record = output_manifest_record(receipt_stage, FINAL_RECEIPT)
        full_bound_names = DECLARED_OUTPUT_NAMES - {FINAL_DECISION}
        full_manifest = sorted(
            [*pre_final_manifest, receipt_record], key=lambda row: row["path"]
        )
        if len(full_manifest) != len(full_bound_names):
            raise RuntimeError("terminal content manifest cardinality mismatch")
        verify_output_manifest(pre_final_manifest, pre_final_names)
        if output_manifest_record(receipt_stage, FINAL_RECEIPT) != receipt_record:
            raise RuntimeError("staged receipt content drift")

        measurements = dict(receipt_measurements)
        measurements["authoritativeOuterFinalizationPass"] = True
        measurements["completeOutputManifestPass"] = True
        promotion = (
            provisional["scientific_promotion_pass_provisional"]
            and all(measurements[name] for name in (
                "hardMemoryEnvelopePass",
                "activeHorizonAccessDeniedPass",
                "ownedCgroupLifecyclePass",
                "authoritativeOuterFinalizationPass",
                "completeOutputManifestPass",
            ))
        )
        decision = {
            "schema": (
                "gamma.enwiki9.wiki-fiber-fossil-endpoint428-"
                "opening1m-authoritative-decision.v2"
            ),
            "candidate_id": CANDIDATE_ID,
            "authoritative": True,
            "sole_authority": True,
            "status": "passed" if promotion else "failed",
            "measurements": measurements,
            "receipt": receipt_record,
            "authoritative_cgroup": cgroup,
            "complete_output_manifest": {
                "policy": "exact-path-bytes-sha256-decision-self-excluded-v1",
                "entries": full_manifest,
                "declared_artifact_count": len(DECLARED_OUTPUT_NAMES),
                "bound_artifact_count": len(full_manifest),
                "exact_once_pass": True,
                "decision_self_exclusion": {
                    "path": f"results/{CANDIDATE_ID}/{FINAL_DECISION}",
                    "reason": "A file cannot contain its own SHA-256; this sole authority is atomically published last.",
                },
            },
            "next_action": (
                "authorize only one separately frozen native Fiber-FOSSIL P/K/D gate"
                if promotion
                else "retire semantic-distance exact retrieval before LOOM or route fast weights"
            ),
            "archive_authority": False,
            "score_credit_bytes": 0,
        }
        decision_stage = write_staged_json("decision", decision)
        staged_decision_sha256 = sha256(decision_stage)
        if failure_injector is not None:
            failure_injector("before_publish")
        verify_output_manifest(pre_final_manifest, pre_final_names)
        if output_manifest_record(receipt_stage, FINAL_RECEIPT) != receipt_record:
            raise RuntimeError("staged receipt drifted before publish")

        publish_staged_file(receipt_stage, RESULT / FINAL_RECEIPT)
        receipt_stage = None
        if failure_injector is not None:
            failure_injector("after_receipt_publish")
        verify_output_manifest(full_manifest, full_bound_names)

        publish_staged_file(decision_stage, RESULT / FINAL_DECISION)
        decision_stage = None
        published = True
        if failure_injector is not None:
            failure_injector("after_decision_publish")
        require_exact_output_names(DECLARED_OUTPUT_NAMES)
        verify_output_manifest(
            full_manifest, full_bound_names, DECLARED_OUTPUT_NAMES
        )
        if sha256(RESULT / FINAL_DECISION) != staged_decision_sha256:
            raise RuntimeError("terminal decision drifted during atomic publish")
        observed_decision = json.loads((RESULT / FINAL_DECISION).read_text())
        if observed_decision != decision or observed_decision.get(
            "authoritative"
        ) is not True:
            raise RuntimeError("terminal decision authority verification failed")
    except Exception:
        rollback_authority_files()
        raise
    finally:
        for staged in (decision_stage, receipt_stage):
            if staged is not None and (staged.is_file() or staged.is_symlink()):
                staged.unlink()
    if not published:
        raise RuntimeError("terminal decision was not atomically published")


def synthetic_worker() -> int:
    global RESULT
    install_horizon_access_guard()
    memory_envelope = apply_hard_rlimit()
    memory_envelope["cgroup"] = cgroup_memory_envelope(True)
    original_result = RESULT
    with tempfile.TemporaryDirectory(
        prefix="gamma-fiber-receiptfix-validation-",
        dir=PROJECT / "results",
    ) as temporary:
        validation_root = Path(temporary)
        under_guarded_root = validation_root.parent.resolve() in HORIZON_RESULT_ROOTS
        if not under_guarded_root:
            raise RuntimeError("validation directory is outside guarded results")
        RESULT = validation_root
        try:
            denial_before = HORIZON_DENIAL_COUNT
            probe = perform_guarded_horizon_probe()
            probe_path = RESULT / HORIZON_PROBE
            published = artifact(probe_path)
            publication_verified = (
                json.loads(probe_path.read_text()) == probe
                and HORIZON_DENIAL_COUNT == denial_before + 1
                and {path.name for path in RESULT.iterdir()} == {HORIZON_PROBE}
            )
            if not publication_verified:
                raise RuntimeError("synthetic denial receipt publication failed")
        finally:
            RESULT = original_result
    directory_removed = not validation_root.exists()
    if not directory_removed:
        raise RuntimeError("synthetic denial receipt directory was not removed")
    print(json.dumps({
        "synthetic_worker": True,
        "corpus_accessed": False,
        "hard_rlimit_as": memory_envelope,
        "horizon_access_denied": probe["denied_before_corpus"],
        "normal_denial_probe_function_exercised": True,
        "denial_receipt_publication_verified": publication_verified,
        "denial_receipt": published,
        "denial_receipt_output_basename": HORIZON_PROBE,
        "validation_directory_under_guarded_result_root": under_guarded_root,
        "validation_directory_removed": directory_removed,
    }, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--snapshot-root", type=Path)
    parser.add_argument("--guarded-worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--synthetic-worker", action="store_true", help=argparse.SUPPRESS)
    arguments = parser.parse_args(argv)
    if arguments.synthetic_worker:
        return synthetic_worker()
    install_horizon_access_guard()
    memory_envelope = apply_hard_rlimit()
    snapshot_root = _snapshot_root(arguments.snapshot_root)
    if arguments.guarded_worker:
        if arguments.snapshot_root is not None:
            raise RuntimeError("guarded worker accepts only adaptive snapshot environment")
        memory_envelope["cgroup"] = cgroup_memory_envelope(True)
        horizon_probe = perform_guarded_horizon_probe()
        return run_gate(memory_envelope, horizon_probe)
    if arguments.validate_only:
        memory_envelope["cgroup"] = cgroup_memory_envelope(False)
        validation = validate_only(snapshot_root, memory_envelope)
        command = [sys.executable, str(Path(__file__).resolve()), "--synthetic-worker"]
        returncode, output, cgroup = launch_in_owned_cgroup(
            command, HARD_MEMORY_LIMIT_BYTES, True
        )
        if returncode != 0:
            raise RuntimeError(f"synthetic cgroup worker failed: {output}")
        synthetic = json.loads(output)
        validation["synthetic_cgroup_admission_cleanup"] = {
            "worker": synthetic,
            "cgroup": cgroup,
            "owned_cgroup_removed": not (
                DELEGATED_CGROUP_PARENT / cgroup["owned_name"]
            ).exists(),
        }
        print(json.dumps(validation, sort_keys=True))
        return 0
    if arguments.snapshot_root is not None:
        raise RuntimeError("--snapshot-root is allowed only with --validate-only")
    command = [sys.executable, str(Path(__file__).resolve()), "--guarded-worker"]
    returncode, _output, cgroup = launch_in_owned_cgroup(
        command, HARD_MEMORY_LIMIT_BYTES, False
    )
    if returncode == 0:
        finalize_authoritative_result(cgroup)
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
