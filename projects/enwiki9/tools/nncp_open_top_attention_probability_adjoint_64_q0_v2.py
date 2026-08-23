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
import tarfile
import tempfile
import traceback
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_attention_probability_adjoint_64_q0_v2"
RESULT = ROOT / "results" / CANDIDATE_ID
PROGRAM = ROOT / "programs" / CANDIDATE_ID
SOURCE = PROGRAM / "attention_probability_adjoint.cpp"
META = PROGRAM / "meta.json"
DESCRIPTOR = PROGRAM / "program.py"
CONTRACT = ROOT / "operations/planning/nncp_open_top_attention_probability_adjoint_64_q0_v2.json"
PROPOSAL = ROOT / "operations/adaptive/proposals/proposed/000_nncp_open_top_attention_probability_adjoint_64_q0_v2.json"
LEASE = ROOT / "operations/runtime/exclusive_full1g.json"

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

COMPILER = Path("/home/x/enwiki9-nonproof/toolchains/clang17/root/usr/bin/clang++-17")
TOOLCHAIN_LIB = COMPILER.parents[1] / "lib/x86_64-linux-gnu"
LLVM_BIN = Path("/home/x/enwiki9-nonproof/cmix-obias-donor/cmix-obias/tools/llvm17-local/bin")
LINKER = LLVM_BIN / "ld.lld"
FLAGS = [
    "-std=c++17", "-O3", "-mavx2", "-mfma", "-ffp-contract=off",
    "-fno-fast-math", "-fno-associative-math", "-fuse-ld=lld",
    "-Wall", "-Wextra", "-Werror",
]
ENVIRONMENT = {
    "PATH": f"{LLVM_BIN}:/usr/bin:/bin",
    "LD_LIBRARY_PATH": str(TOOLCHAIN_LIB),
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


def source_package(path: Path) -> None:
    members = sorted((SOURCE, META, DESCRIPTOR, Path(__file__).resolve(), CONTRACT, PROPOSAL),
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
    for path in (SOURCE, META, DESCRIPTOR, CONTRACT, PROPOSAL, COMPILER, LINKER):
        if not path.is_file():
            raise FileNotFoundError(path)
    verify(VALUE, VALUE_BYTES, VALUE_SHA256, "value state")
    verify(ATTENDED, ATTENDED_BYTES, ATTENDED_SHA256, "attended adjoint")
    verify(SOURCE_ADJOINT, OUTPUT_BYTES, SOURCE_SHA256, "source probability adjoint")
    antecedents = []
    for relative, expected in ANTECEDENTS:
        path = ROOT / relative
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"antecedent drift: {relative}")
        antecedents.append(artifact(path))
    if RESULT.exists():
        raise FileExistsError(f"refusing to overwrite {RESULT}")
    RESULT.mkdir(parents=True)
    decision: dict[str, Any] = {
        "schema": "gamma.enwiki9.nncp_open_attention_probability_adjoint.v2",
        "candidate_id": CANDIDATE_ID,
        "operational_status": "running",
        "claim_authority": "none",
        "objective_credit_bytes": 0,
        "promotion_authorized": False,
        "antecedents": antecedents,
        "inputs": {"value": artifact(VALUE), "attended": artifact(ATTENDED),
                   "source_probability_adjoint": artifact(SOURCE_ADJOINT)},
        "program": {"source": artifact(SOURCE), "contract": artifact(CONTRACT),
                    "proposal": artifact(PROPOSAL), "compiler": artifact(COMPILER),
                    "linker": artifact(LINKER), "flags": FLAGS},
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
            for replay in ("a", "b"):
                paths = {name: work / f"{name}-{replay}.bf16" for name in names}
                receipt = run([str(evaluator), str(VALUE), str(ATTENDED),
                               *(str(paths[name]) for name in names)], work,
                              RESULT / f"evaluation-{replay}.stdout",
                              RESULT / f"evaluation-{replay}.stderr")
                if receipt["returncode"] != 0:
                    raise RuntimeError(f"evaluation {replay} failed")
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

        source_package(RESULT / "incremental_source.tar.xz")
        comparisons = decision["execution"]["comparisons"]
        gates = {
            "complete_population": all(row["elements"] == ELEMENTS for row in comparisons.values()),
            "scalar_source_exact": comparisons["scalar_source"]["mismatch_count"] == 0,
            "avx_source_exact": comparisons["avx_source"]["mismatch_count"] == 0,
            "scalar_avx_exact": comparisons["scalar_avx"]["mismatch_count"] == 0,
            "wrong_layout_control_live": comparisons["wrong_layout_source"]["mismatch_count"] > 0,
            "negated_control_live": comparisons["negated_source"]["mismatch_count"] > 0,
            "repeat_byte_identity": decision["execution"]["replay_identity"],
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
