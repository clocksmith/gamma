#!/usr/bin/env python3
"""Run the versioned scalar and AVX attention-probability adjoint gate."""

from __future__ import annotations

import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import traceback
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_attention_probability_adjoint_64_q0_v2"
EXPERIMENT_ID = "nncp_open_top_attention_probability_adjoint_64_q0_v2_gate"
RESULT = ROOT / "results" / CANDIDATE_ID
PROGRAM = ROOT / "programs" / CANDIDATE_ID
SOURCE = PROGRAM / "attention_probability_adjoint.cpp"
META = PROGRAM / "meta.json"
DESCRIPTOR = PROGRAM / "program.py"
CONTRACT = ROOT / "operations/planning/nncp_open_top_attention_probability_adjoint_64_q0_v2.json"
TOOLCHAIN_CONTRACT = ROOT / "operations/planning/nncp_open_top_attention_probability_adjoint_64_q0_v2_toolchain.json"
EXPERIMENT = ROOT / "operations/adaptive/experiments" / f"{EXPERIMENT_ID}.json"
LEASE = ROOT / "operations/runtime/exclusive_full1g.json"
RESOURCE_GUARD = ROOT / "tools/run_with_resource_guard_v3.py"
TASKSET = Path("/usr/bin/taskset")
SHELL = Path("/bin/sh")
RESOURCE_MEMORY_BYTES = 10_000_000_000
TEMPORARY_DISK_LIMIT_BYTES = 2_000_000_000

VALUE = ROOT / "results/nncp_open_top_attention_forward_inputs_64_q0_v1/open-exact-value-state.bf16"
ATTENDED = ROOT / "results/nncp_open_concat_head_identity_64_q0_v1/open-exact-attended-adjoint.bf16"
SOURCE_ADJOINT = ROOT / "results/nncp_libnc_top_attention_product_oracle_64_q0_retry_v2/source-attention-probability-adjoint.bf16"
VALUE_BYTES = 20_971_520
ATTENDED_BYTES = 4_194_304
OUTPUT_BYTES = 10_485_760
VALUE_SHA256 = "71968ffd71811ef06db7064c675872bcbd98344abd7e9d09f2231dd538e3f790"
ATTENDED_SHA256 = "481b6d3c8ec04a8302adca1ed7c0d43ad47c2459aa4586b4950726af05c2e27a"
SOURCE_SHA256 = "94763dc5ad7c78020c2620a06b0824fd7f2280c6a2a4c3783618931da44dbe22"
ELEMENTS = 5_242_880
SOURCE_CEILING = 500_000

COMPILER = Path("/usr/bin/x86_64-linux-gnu-g++-15")
LINKER = Path("/usr/bin/x86_64-linux-gnu-ld")
FLAGS = [
    "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-pedantic",
    "-mavx2", "-mfma", "-fno-fast-math", "-fno-associative-math",
    "-ffp-contract=off", "-march=x86-64", "-mtune=generic",
    "-Wl,--build-id=none",
]
ENVIRONMENT = {
    "PATH": "/usr/bin:/bin",
    "LANG": "C",
    "LC_ALL": "C",
    "TZ": "UTC",
    "SOURCE_DATE_EPOCH": "0",
}

ANTECEDENTS = [
    ("results/nncp_open_top_attention_forward_inputs_64_q0_v1/decision.json", "67e97ef019583d4fe6e8d7d31b62c5b2b4bc1494350dea62519c23fbf8086558"),
    ("results/nncp_open_top_attention_forward_inputs_64_q0_v1/execution.json", "713a9c20bb48bb4b0eebea831d48f5867a8bccb47095f57155780684461a1f0d"),
    ("results/nncp_open_top_attention_forward_inputs_64_q0_v1/guard.json", "2e9ffa542921cdc3748d53737aa959c71d3bc87d6179b0d48d23b1837d4e966c"),
    ("operations/adaptive/reflections/20260816T220926Z_56872cd576.json", "6629f6923b631c87e7ff83fbfc8787c4590bc4b7be50c84178faf94e00b1022d"),
    ("results/nncp_libnc_top_attention_product_oracle_64_q0_retry_v2/decision.json", "e9011ea1891c14d82db1d3c1d733f183efaf63c1c04091fa91d9e4debd14a37d"),
    ("results/nncp_libnc_top_attention_product_oracle_64_q0_retry_v2/execution.json", "4fd30f759b0665a48a5359d6382e0d8520bd211a2b719a39d564add94ae31b4c"),
    ("results/nncp_libnc_top_attention_product_oracle_64_q0_retry_v2/guard.json", "4978f9d430bf78eaf69d992e995deeb4b9af18ea951c8f41f1df4a9543e9fa31"),
    ("operations/adaptive/reflections/20260816T174722Z_8b88b4a53d.json", "a2191bedd789d7f7ca55076d87c36cf367ba6789ec0cbc380cbfaa7077b2083a"),
    ("results/nncp_open_concat_head_identity_64_q0_v1/decision.json", "f0dc7bf5832700ac458be3cd0bdddfb8fb4a2f1c7242d1a14e180ccf6fd155e5"),
    ("results/nncp_open_concat_head_identity_64_q0_v1/execution.json", "fe3b310868a9a702b81eb4c1061d591acd39a2e46103794b45bdccd31998a4b0"),
    ("results/nncp_open_concat_head_identity_64_q0_v1/guard.json", "40e3e3865fa6664ef5cdfbc0055ebce6c52018cfd6f0a157b4ee585d759efac0"),
    ("operations/adaptive/reflections/20260816T175422Z_91aae07812.json", "a05c513aebdef149e64e3aab32bf6fbc969449632de744a9057ed17357692859"),
    ("results/nncp_open_w_o_input_adjoint_block128_64_q0_v1/decision.json", "a3a5b8b76cd878ac904acd2b674a2972b0a13c740d8a2748ef18977c16f1ed75"),
    ("results/nncp_open_w_o_input_adjoint_block128_64_q0_v1/execution.json", "2ca946fa990a0b07ab6c70c0fdda90f54a4f0b491ba4abce76793db828df4ede"),
    ("results/nncp_open_w_o_input_adjoint_block128_64_q0_v1/guard.json", "c5a43f9f7d3446521259ca8a0366c9842466960329e58ab9ba984dd623504fa6"),
    ("operations/adaptive/reflections/20260816T164348Z_ff5718724e.json", "35c9bd3b0c90adcf69f2620f8544b559765e10d19d219c8a43c604a4ef6ee008"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def bound_proposal() -> Path:
    matches = []
    for state in ("developed", "claimed", "proposed"):
        matches.extend(
            (ROOT / "operations" / "adaptive" / "proposals" / state).glob(
                f"*_{EXPERIMENT_ID}.json"
            )
        )
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one bound {EXPERIMENT_ID} proposal, found {len(matches)}"
        )
    return matches[0]


def verify_adaptive_bindings() -> dict[str, Any]:
    raw_revision = os.environ.get("GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON")
    raw_experiment = os.environ.get("GAMMA_ENWIKI9_EXPERIMENT_JSON")
    snapshot_id = os.environ.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ID")
    snapshot_root = os.environ.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT")
    if not all((raw_revision, raw_experiment, snapshot_id, snapshot_root)):
        raise RuntimeError("revision-bound adaptive execution environment is required")
    revision = json.loads(raw_revision)
    experiment_reference = json.loads(raw_experiment)
    if revision.get("candidateId") != CANDIDATE_ID or snapshot_id != CANDIDATE_ID:
        raise RuntimeError("adaptive candidate identity mismatch")
    expected_experiment_path = EXPERIMENT.relative_to(ROOT).as_posix()
    if experiment_reference.get("path") != expected_experiment_path:
        raise RuntimeError("adaptive experiment path mismatch")
    expected_experiment_sha256 = experiment_reference.get("sha256")
    if expected_experiment_sha256 != f"sha256:{sha256(EXPERIMENT)}":
        raise RuntimeError("adaptive experiment digest mismatch")
    snapshot = Path(snapshot_root).resolve(strict=True)
    for relative, live in (
        ("attention_probability_adjoint.cpp", SOURCE),
        ("meta.json", META),
        ("program.py", DESCRIPTOR),
    ):
        sealed = snapshot / relative
        if not sealed.is_file() or sha256(sealed) != sha256(live):
            raise RuntimeError(f"sealed candidate snapshot differs: {relative}")
    return {
        "candidate_revision": revision,
        "experiment": experiment_reference,
        "snapshot_root": str(snapshot),
    }


def verify_toolchain() -> dict[str, Any]:
    contract = json.loads(TOOLCHAIN_CONTRACT.read_text(encoding="utf-8"))
    if contract.get("candidate_id") != CANDIDATE_ID or contract.get("flags") != FLAGS:
        raise RuntimeError("pinned toolchain contract differs from runner")
    records = [contract.get("compiler"), contract.get("linker"), *contract.get("tools", [])]
    for record in records:
        if not isinstance(record, dict):
            raise RuntimeError("malformed pinned toolchain record")
        path = Path(str(record.get("path", "")))
        if not path.is_file() or sha256(path) != record.get("sha256"):
            raise RuntimeError(f"pinned tool identity mismatch: {path}")
    compiler_line = subprocess.run(
        [str(COMPILER), "--version"], env=ENVIRONMENT, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.splitlines()[0]
    linker_line = subprocess.run(
        [str(LINKER), "--version"], env=ENVIRONMENT, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.splitlines()[0]
    if compiler_line != contract["compiler"]["version_line"]:
        raise RuntimeError("pinned compiler version line mismatch")
    if linker_line != contract["linker"]["version_line"]:
        raise RuntimeError("pinned linker version line mismatch")
    return {
        "contract": artifact(TOOLCHAIN_CONTRACT),
        "compiler_version_line": compiler_line,
        "linker_version_line": linker_line,
    }


def write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def proc_start_ticks(pid: int) -> int | None:
    try:
        return int(Path(f"/proc/{pid}/stat").read_text().split()[21])
    except (FileNotFoundError, IndexError, ValueError):
        return None


def assert_exclusive_host_released() -> None:
    if not LEASE.is_file():
        return
    lease = json.loads(LEASE.read_text(encoding="utf-8"))
    if isinstance(lease.get("pid"), int) and proc_start_ticks(lease["pid"]) == lease.get("proc_start_ticks"):
        raise RuntimeError("exclusive full-1G lease remains active")
    if isinstance(lease.get("codec_pid"), int) and Path(f"/proc/{lease['codec_pid']}").exists():
        raise RuntimeError("exclusive full-1G codec PID still exists")


def verify(path: Path, expected_bytes: int, expected_sha256: str, label: str) -> None:
    if not path.is_file() or path.stat().st_size != expected_bytes or sha256(path) != expected_sha256:
        raise RuntimeError(f"{label} identity mismatch")


def run(argv: list[str], cwd: Path, stdout: Path, stderr: Path) -> dict[str, Any]:
    completed = subprocess.run(argv, cwd=cwd, env=ENVIRONMENT, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, check=False)
    stdout.write_bytes(completed.stdout)
    stderr.write_bytes(completed.stderr)
    return {"argv": argv, "cwd": str(cwd), "environment": ENVIRONMENT,
            "returncode": completed.returncode, "stdout": artifact(stdout),
            "stderr": artifact(stderr)}


def require_empty_cgroup(environment_name: str) -> Path:
    raw = os.environ.get(environment_name)
    if not raw:
        raise RuntimeError(f"{environment_name} must name a pre-created empty cgroup v2 directory")
    path = Path(raw)
    procs = path / "cgroup.procs"
    if not path.is_dir() or not procs.is_file():
        raise RuntimeError(f"invalid cgroup v2 directory in {environment_name}: {path}")
    if procs.read_text(encoding="ascii").strip():
        raise RuntimeError(f"cgroup is not empty: {path}")
    return path


def verify_resource_guard_receipt(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"path": str(path), "terminal_pass": False, "reason": "receipt absent"}
    value = json.loads(path.read_text(encoding="utf-8"))
    measurements = value.get("measurements")
    guards = value.get("guards")
    cgroup = value.get("cgroup")
    terminal_pass = (
        value.get("schema") == "gamma.enwiki9.resource-guard-receipt.v3"
        and value.get("status") == "complete"
        and value.get("returncode") == 0
        and isinstance(measurements, dict)
        and bool(measurements)
        and all(item is True for item in measurements.values())
        and isinstance(guards, dict)
        and bool(guards)
        and all(item is False for item in guards.values())
        and isinstance(cgroup, dict)
        and cgroup.get("joined_before_exec") is True
    )
    return {
        "artifact": artifact(path),
        "terminal_pass": terminal_pass,
        "status": value.get("status"),
        "returncode": value.get("returncode"),
        "cgroup_joined_before_exec": cgroup.get("joined_before_exec") if isinstance(cgroup, dict) else None,
    }


def run_guarded_evaluation(
    evaluator: Path,
    paths: dict[str, Path],
    replay: str,
    work: Path,
    cgroup: Path,
    cpu: int,
) -> dict[str, Any]:
    marker = work / f"evaluation-{replay}.phase-markers.jsonl"
    marker.write_bytes(b"")
    guard_path = RESULT / f"evaluation-{replay}.guard.json"
    begin = json.dumps(
        {"detail": f"evaluation-{replay}", "event": "begin", "phase": "diagnostic"},
        sort_keys=True,
        separators=(",", ":"),
    )
    end = json.dumps(
        {"detail": f"evaluation-{replay}", "event": "end", "phase": "diagnostic"},
        sort_keys=True,
        separators=(",", ":"),
    )
    script = (
        f"printf '%s\\n' '{begin}' >> \"$GAMMA_RESOURCE_PHASE_MARKERS\"\n"
        "\"$@\"\n"
        "rc=$?\n"
        f"printf '%s\\n' '{end}' >> \"$GAMMA_RESOURCE_PHASE_MARKERS\"\n"
        "exit \"$rc\"\n"
    )
    child = [
        str(TASKSET), "-c", str(cpu), str(SHELL), "-c", script,
        "guarded-evaluator", str(evaluator), str(VALUE), str(ATTENDED),
        *(str(paths[name]) for name in ("scalar", "avx", "wrong_layout", "negated")),
    ]
    argv = [
        sys.executable,
        str(RESOURCE_GUARD),
        "--limit-mode", "tree",
        "--limit-kib", "9765625",
        "--official-decimal-limit-kib", "9765625",
        "--sample-interval", "0.5",
        "--cgroup-path", str(cgroup),
        "--cgroup-memory-max-bytes", str(RESOURCE_MEMORY_BYTES),
        "--scratch-path", str(work),
        "--temporary-disk-limit-bytes", str(TEMPORARY_DISK_LIMIT_BYTES),
        "--phase-marker-path", str(marker),
        "--smaps-growth-checkpoint-kib", "65536",
        "--max-smaps-checkpoints", "128",
        "--max-logical-cpus", "1",
        "--guard-json", str(guard_path),
        "--label", f"{CANDIDATE_ID}-{replay}",
        "--phase", "diagnostic",
        "--",
        *child,
    ]
    invocation = run(
        argv,
        work,
        RESULT / f"evaluation-{replay}.stdout",
        RESULT / f"evaluation-{replay}.stderr",
    )
    guard = verify_resource_guard_receipt(guard_path)
    if invocation["returncode"] != 0 or guard["terminal_pass"] is not True:
        raise RuntimeError(f"evaluation {replay} external resource guard failed")
    return {"invocation": invocation, "resource_guard": guard}


def bf16_float(word: int) -> float:
    return struct.unpack("<f", struct.pack("<I", word << 16))[0]


def compare(left: Path, right: Path) -> dict[str, Any]:
    left_bytes = left.read_bytes()
    right_bytes = right.read_bytes()
    if len(left_bytes) != len(right_bytes) or len(left_bytes) % 2 != 0:
        raise RuntimeError("BF16 comparator geometry mismatch")
    mismatches = 0
    maximum = 0.0
    for offset in range(0, len(left_bytes), 2):
        a = left_bytes[offset] | (left_bytes[offset + 1] << 8)
        b = right_bytes[offset] | (right_bytes[offset + 1] << 8)
        if a != b:
            mismatches += 1
            maximum = max(maximum, abs(bf16_float(a) - bf16_float(b)))
    return {"elements": len(left_bytes) // 2, "mismatch_count": mismatches,
            "maximum_absolute_error": maximum}


def source_package(path: Path, proposal: Path) -> None:
    members = sorted((SOURCE, META, DESCRIPTOR, Path(__file__).resolve(), RESOURCE_GUARD,
                      ROOT / "tools/research_contracts.py",
                      ROOT / "tools/enwiki9_python_source_closure.py",
                      ROOT / "contracts/research/v1/objective-contract.json",
                      ROOT / "contracts/research/v1/objective-contract.schema.json",
                      CONTRACT, TOOLCHAIN_CONTRACT, EXPERIMENT, proposal),
                     key=lambda item: str(item.relative_to(ROOT)))
    tar_path = path.with_suffix("")
    with tarfile.open(tar_path, "w") as archive:
        for member in members:
            info = archive.gettarinfo(str(member), arcname=str(member.relative_to(ROOT)))
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = ""
            info.mode = 0o644
            with member.open("rb") as handle:
                archive.addfile(info, handle)
    path.write_bytes(lzma.compress(tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME))
    tar_path.unlink()
    if path.stat().st_size > SOURCE_CEILING:
        raise RuntimeError("incremental source package exceeds ceiling")


def main() -> int:
    assert_exclusive_host_released()
    proposal = bound_proposal()
    adaptive_bindings = verify_adaptive_bindings()
    for path in (SOURCE, META, DESCRIPTOR, CONTRACT, TOOLCHAIN_CONTRACT, EXPERIMENT,
                 proposal, COMPILER,
                 LINKER, RESOURCE_GUARD, TASKSET, SHELL):
        if not path.is_file():
            raise FileNotFoundError(path)
    cgroups = [require_empty_cgroup("GAMMA_NNCP_CGROUP_A"), require_empty_cgroup("GAMMA_NNCP_CGROUP_B")]
    if cgroups[0].resolve() == cgroups[1].resolve():
        raise RuntimeError("GAMMA_NNCP_CGROUP_A and GAMMA_NNCP_CGROUP_B must be distinct")
    try:
        cpu = int(os.environ["GAMMA_NNCP_CPU"])
    except (KeyError, ValueError) as error:
        raise RuntimeError("GAMMA_NNCP_CPU must be a nonnegative logical CPU index") from error
    if cpu < 0:
        raise RuntimeError("GAMMA_NNCP_CPU must be a nonnegative logical CPU index")
    verify(VALUE, VALUE_BYTES, VALUE_SHA256, "value state")
    verify(ATTENDED, ATTENDED_BYTES, ATTENDED_SHA256, "attended adjoint")
    verify(SOURCE_ADJOINT, OUTPUT_BYTES, SOURCE_SHA256, "source probability adjoint")
    toolchain = verify_toolchain()
    antecedents = []
    for relative, expected in ANTECEDENTS:
        path = ROOT / relative
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"antecedent drift: {relative}")
        antecedents.append(artifact(path))
    if RESULT.exists():
        if not RESULT.is_dir() or any(RESULT.iterdir()):
            raise FileExistsError(f"refusing to overwrite nonempty {RESULT}")
    else:
        RESULT.mkdir(parents=True)
    decision: dict[str, Any] = {
        "schema": "gamma.enwiki9.nncp_open_attention_probability_adjoint.v2",
        "candidate_id": CANDIDATE_ID,
        "operational_status": "running",
        "claim_authority": "none",
        "objective_credit_bytes": 0,
        "promotion_authorized": False,
        "adaptive_bindings": adaptive_bindings,
        "toolchain": toolchain,
        "antecedents": antecedents,
        "inputs": {"value": artifact(VALUE), "attended": artifact(ATTENDED),
                   "source_probability_adjoint": artifact(SOURCE_ADJOINT)},
        "program": {"source": artifact(SOURCE), "contract": artifact(CONTRACT),
                    "experiment": artifact(EXPERIMENT), "proposal": artifact(proposal),
                    "compiler": artifact(COMPILER),
                    "linker": artifact(LINKER), "resource_guard": artifact(RESOURCE_GUARD),
                    "flags": FLAGS},
        "resource_contract": {
            "cpu": cpu,
            "cgroups": [str(path) for path in cgroups],
            "memory_max_bytes": RESOURCE_MEMORY_BYTES,
            "temporary_disk_limit_bytes": TEMPORARY_DISK_LIMIT_BYTES,
            "limit_mode": "tree",
        },
    }
    try:
        with tempfile.TemporaryDirectory(prefix=f"{CANDIDATE_ID}-", dir="/dev/shm") as temporary:
            work = Path(temporary)
            evaluator = work / "evaluator"
            decision["build"] = run([str(COMPILER), *FLAGS, str(SOURCE), "-o", str(evaluator)],
                                    ROOT, RESULT / "build.stdout", RESULT / "build.stderr")
            if decision["build"]["returncode"] != 0:
                raise RuntimeError("evaluator build failed")
            shutil.copy2(evaluator, RESULT / "evaluator")
            ldd = run(["/usr/bin/ldd", str(evaluator)], ROOT,
                      RESULT / "ldd.stdout", RESULT / "ldd.stderr")
            if ldd["returncode"] != 0:
                raise RuntimeError("ldd failed")
            forbidden = [line for line in (RESULT / "ldd.stdout").read_text().splitlines()
                         if any(token in line.lower() for token in
                                ("libnc", "ggml", "cuda", "openmp", "gomp", "blas"))]

            names = ("scalar", "avx", "wrong_layout", "negated")
            outputs: list[dict[str, Path]] = []
            evaluations = []
            for replay_index, replay in enumerate(("a", "b")):
                paths = {name: work / f"{name}-{replay}.bf16" for name in names}
                receipt = run_guarded_evaluation(
                    evaluator, paths, replay, work, cgroups[replay_index], cpu
                )
                for name, path in paths.items():
                    if path.stat().st_size != OUTPUT_BYTES:
                        raise RuntimeError(f"{name} {replay} geometry mismatch")
                evaluations.append({"receipt": receipt,
                                    "outputs": {name: artifact(path) for name, path in paths.items()}})
                outputs.append(paths)

            replay_identity = all(outputs[0][name].read_bytes() == outputs[1][name].read_bytes()
                                  for name in names)
            comparisons = {
                "scalar_source": compare(outputs[0]["scalar"], SOURCE_ADJOINT),
                "avx_source": compare(outputs[0]["avx"], SOURCE_ADJOINT),
                "scalar_avx": compare(outputs[0]["scalar"], outputs[0]["avx"]),
                "wrong_layout_source": compare(outputs[0]["wrong_layout"], SOURCE_ADJOINT),
                "negated_source": compare(outputs[0]["negated"], SOURCE_ADJOINT),
            }
            shutil.copy2(outputs[0]["avx"], RESULT / "open-exact-probability-adjoint.bf16")
            decision["execution"] = {"evaluations": evaluations, "comparisons": comparisons,
                                     "replay_identity": replay_identity,
                                     "forbidden_dynamic_dependencies": forbidden, "ldd": ldd}

        source_package(RESULT / "incremental_source.tar.xz", proposal)
        comparisons = decision["execution"]["comparisons"]
        gates = {
            "complete_population": all(row["elements"] == ELEMENTS for row in comparisons.values()),
            "scalar_source_exact": comparisons["scalar_source"]["mismatch_count"] == 0,
            "avx_source_exact": comparisons["avx_source"]["mismatch_count"] == 0,
            "scalar_avx_exact": comparisons["scalar_avx"]["mismatch_count"] == 0,
            "wrong_layout_control_live": comparisons["wrong_layout_source"]["mismatch_count"] > 0,
            "negated_control_live": comparisons["negated_source"]["mismatch_count"] > 0,
            "repeat_byte_identity": decision["execution"]["replay_identity"],
            "external_resource_receipts_pass": all(
                evaluation["receipt"]["resource_guard"]["terminal_pass"] is True
                for evaluation in decision["execution"]["evaluations"]
            ),
            "dependency_closure_pass": not decision["execution"]["forbidden_dynamic_dependencies"],
            "source_package_pass": (RESULT / "incremental_source.tar.xz").stat().st_size <= SOURCE_CEILING,
            "work_cleanup_pass": True,
        }
        passed = all(gates.values())
        decision.update({"operational_status": "terminal", "gates": gates,
                         "arithmetic_edge_pass": passed,
                         "scientific_verdict": "authorize_bounded_open_backward_successor" if passed else "retire_probability_adjoint_v2",
                         "next_authority": "at most three additional primitives before integrated segment replay" if passed else "none except one correction-only implementation successor",
                         "artifacts": {"evaluator": artifact(RESULT / "evaluator"),
                                       "probability_adjoint": artifact(RESULT / "open-exact-probability-adjoint.bf16"),
                                       "incremental_source": artifact(RESULT / "incremental_source.tar.xz")}})
    except Exception as exc:
        decision.update({"operational_status": "terminal_infrastructure_failure",
                         "error": f"{type(exc).__name__}: {exc}",
                         "traceback": traceback.format_exc(),
                         "scientific_verdict": "none",
                         "next_authority": "one correction-only implementation successor with unchanged tensors, arithmetic, controls, and comparators"})
        write_json(RESULT / "decision.json", decision)
        return 1
    write_json(RESULT / "decision.json", decision)
    return 0 if decision["arithmetic_edge_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
