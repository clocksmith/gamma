#!/usr/bin/env python3
"""Same native FX2 build, four argmax arms, exact coder records and inverses."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
ID = "fx2_cmix_transformer_argmax_fixture50051_q0_v1"
RESULT = ROOT / "results" / ID
CONTRACT = ROOT / "operations/adaptive/experiments" / (ID + ".json")
SOURCE = ROOT / "external/fx2-cmix-transformer-v1"
PARENT = ROOT / "results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1"
FAST = "-DSEED=923 -DUPDATE_LIMIT=3000 -m64 -Wall -std=c++17 -include cstdint -fno-fast-math -fno-math-errno -fno-exceptions -fno-threadsafe-statics -march=x86-64-v3 -mtune=generic -mrecip=none -fdata-sections -ffunction-sections"
ARMS = ("P", "K", "D", "C")
TIMING_ORDER = ("P", "K", "D", "C", "C", "D", "K", "P")
MODELED_BYTES = 32478
TRACE_BYTES = MODELED_BYTES * 8 * 28


def sha(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def verify_inputs() -> dict:
    contract = read(CONTRACT)
    for row in contract["inputs"]:
        path = ROOT / row["path"]
        if path.is_symlink() or sha(path) != row["sha256"].removeprefix("sha256:"):
            raise ValueError("frozen input changed: " + row["path"])
    toolchain = read(ROOT / "operations/provenance/public_fx2_gcc15_toolchain_20260905.json")
    for row in toolchain["toolchain"]:
        if sha(Path(row["path"])) != row["sha256"]:
            raise ValueError("pinned toolchain changed: " + row["name"])
        alias = Path("/usr/bin") / row["name"]
        if alias.exists() and alias.resolve() != Path(row["path"]):
            raise ValueError("toolchain executable alias changed: " + row["name"])
    return contract


def apply_adapter(work: Path, adapter: dict) -> None:
    for row in adapter.get("files", [adapter]):
        path = work / row["source_path"]
        if sha(path) != row["source_sha256"]:
            raise ValueError("adapter preimage changed: " + row["source_path"])
        text = path.read_text()
        for replacement in row["replacements"]:
            if text.count(replacement["before"]) != 1:
                raise ValueError("adapter replacement is not unique")
            text = text.replace(replacement["before"], replacement["after"])
        path.write_text(text)
        if sha(path) != row["patched_sha256"]:
            raise ValueError("adapter postimage differs")


def marker(phase: str, event: str) -> None:
    with Path(os.environ["GAMMA_RESOURCE_PHASE_MARKERS"]).open("a") as handle:
        handle.write(json.dumps({"phase": phase, "event": event}) + "\n")


def execute(name: str, command: list[str], work: Path, cap: int, env: dict | None = None, expected: int = 0) -> dict:
    from lib.artifacts import atomic_write_json
    full = ["/usr/bin/timeout", "--signal=TERM", "--kill-after=5", str(cap), *command]
    marker(name, "start")
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    start = time.monotonic()
    with (RESULT / (name + ".stdout")).open("xb") as out, (RESULT / (name + ".stderr")).open("xb") as err:
        done = subprocess.run(full, cwd=work, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "TMPDIR": str(work / "tmp"), **(env or {})}, stdout=out, stderr=err)
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    record = {"phase": name, "command": full, "environment": env or {}, "returncode": done.returncode, "expected_returncode": expected,
              "elapsed_seconds": time.monotonic() - start, "elapsed_cap_seconds": cap,
              "user_cpu_seconds": after.ru_utime - before.ru_utime,
              "system_cpu_seconds": after.ru_stime - before.ru_stime,
              "timing_authority": "shared-host diagnostic"}
    atomic_write_json(RESULT / (name + ".execution.json"), record)
    marker(name, "end")
    if done.returncode != expected:
        raise RuntimeError(name + " exited " + str(done.returncode))
    return record


class NativeCodec:
    def __init__(self, work: Path, arm: str, binary_sha: str):
        self.work, self.arm, self.binary_sha = work, arm, binary_sha
        self.encodes = 0

    def invoke(self, name: str, arguments: list[str], trace: bool) -> dict:
        if sha(self.work / "cmix") != self.binary_sha:
            raise ValueError("same-build native binary changed")
        env = {"GAMMA_FX2_ARGMAX_ARM": self.arm}
        if trace:
            env["GAMMA_FX2_CODER_TRACE"] = str(self.work / (name + ".trace"))
        record = execute(name, [str(self.work / "cmix"), *arguments], self.work, 120, env)
        lines = (RESULT / (name + ".stderr")).read_bytes().splitlines()
        selections = [line for line in lines if line.startswith(b"Gamma argmax selected=")]
        if selections != [b"Gamma argmax selected=" + self.arm.encode()] * 3:
            raise ValueError("explicit arm activation did not reach all three ByteModels")
        return record

    def compress(self, raw: bytes) -> bytes:
        name = self.arm + ("-encode" if self.encodes == 0 else "-reencode")
        self.encodes += 1
        (self.work / (name + ".raw")).write_bytes(raw)
        self.invoke(name, ["-c", "dictionary/english.dic", name + ".raw", name + ".cmix", "--transformer", "models/6m-q4-fp32.tfwc2"], True)
        return (self.work / (name + ".cmix")).read_bytes()

    def decompress(self, archive: bytes) -> bytes:
        name = self.arm + "-decode"
        (self.work / (name + ".cmix")).write_bytes(archive)
        self.invoke(name, ["-d", "dictionary/english.dic", name + ".cmix", name + ".raw", "--transformer", "models/6m-q4-fp32.tfwc2"], True)
        return (self.work / (name + ".raw")).read_bytes()


def compare_trace(reference: Path, target: Path) -> dict:
    """Exact record comparison with block hashes and retained first divergence."""
    from lib.artifacts import artifact_ref, atomic_write_json
    for path in (reference, target):
        if path.is_symlink() or not path.is_file() or path.stat().st_size != TRACE_BYTES:
            atomic_write_json(RESULT / "first-divergence.json", {"kind": "trace-completeness-failure",
                              "path": str(path.relative_to(ROOT)), "required_bytes": TRACE_BYTES,
                              "observed_bytes": path.stat().st_size if path.exists() else None})
            raise ValueError("coder trace has missing or extra records: " + path.name)
    blocks = []
    offset = 0
    with reference.open("rb") as left, target.open("rb") as right:
        while a := left.read(28 * 4096):
            b = right.read(len(a))
            if a != b:
                first = offset + next(i for i, pair in enumerate(zip(a, b)) if pair[0] != pair[1])
                record = first // 28
                left.seek(max(0, record - 2) * 28)
                right.seek(max(0, record - 2) * 28)
                atomic_write_json(RESULT / "first-divergence.json", {
                    "reference": artifact_ref(reference, ROOT), "target": artifact_ref(target, ROOT),
                    "first_differing_byte": first, "first_differing_bit_record": record,
                    "context_first_record": max(0, record - 2),
                    "reference_context_hex": left.read(28 * 5).hex(), "target_context_hex": right.read(28 * 5).hex()})
                raise ValueError("coder record divergence at bit " + str(record))
            blocks.append({"first_bit_record": offset // 28, "records": len(a) // 28,
                           "sha256": hashlib.sha256(a).hexdigest()})
            offset += len(a)
    return {"target": artifact_ref(target, ROOT), "exact_byte_comparison": True, "blocks": blocks}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    contract = verify_inputs()
    if args.validate_only:
        print(json.dumps({"frozen_inputs_verified": len(contract["inputs"]), "codec_executed": False}))
        return 0
    if os.sched_getaffinity(0) != {2}:
        raise RuntimeError("canonical parent launcher must already be pinned to CPU2")
    if not RESULT.is_dir() or any(RESULT.iterdir()):
        raise RuntimeError("canonical executor must provide an empty result directory")
    sys.path.insert(0, str(ROOT))
    from lib import driver
    from lib.artifacts import artifact_ref, atomic_write_json
    from tools.fx2_cmix_transformer_gcc_fixture50051_q0_v4_materializer import materialize

    stage = {"schema": "gamma.enwiki9.fx2-native-argmax-comparison.v1", "candidate_id": ID,
             "status": "running", "scope_bytes": 50051, "modeled_bytes": MODELED_BYTES,
             "objective_credit_bytes": 0, "larger_gate_authorized": False, "arms": {},
             "continuous_guard_decision": "pending outer canonical guard closure"}
    try:
        audit = read(ROOT / "operations/provenance/public_fx2_cmix_transformer_v1.json")
        work = RESULT / "work"
        materialize(SOURCE, work, audit["build_source_files"])
        (work / "tmp").mkdir()
        for filename in ("public_fx2_static_vocab_adapter_v1.json", "public_fx2_argmax_adapter_v1.json", "public_fx2_argmax_native_adapter_v1.json"):
            adapter = read(ROOT / "operations/provenance" / filename)
            apply_adapter(work, adapter)
            for row in adapter.get("added_files", []):
                source = ROOT / row["source"]["path"]
                if sha(source) != row["source"]["sha256"]:
                    raise ValueError("added adapter source changed")
                shutil.copyfile(source, work / row["destination"])
        execute("compile", ["/usr/bin/make", "-j1", "cmix", "CC=/usr/bin/g++",
                "CPPFLAGS_PART-THAT-SHOULD-BE-FAST=" + FAST + " -O3",
                "CPPFLAGS_PART-THAT-CAN-BE-SLOW=" + FAST + " -Os"], work, 180)
        binary = artifact_ref(work / "cmix", ROOT)
        execute("disassemble", ["/usr/bin/objdump", "-d", "--insn-width=16", "cmix"], work, 30)
        import re
        assembly = (RESULT / "disassemble.stdout").read_text()
        if re.search(r"\b(?:v?(?:rcp|rsqrt)(?:14|28)?(?:ss|ps))\b|%zmm|%k[0-7]|\{vex\}|\t62 [0-9a-f][0-9a-f] ", assembly):
            raise RuntimeError("reciprocal estimate or AVX512 instruction rejected")
        files = [artifact_ref(work / row["path"], ROOT) for row in audit["build_source_files"]]
        files += [artifact_ref(work / "src/coder/gamma-coder-trace.h", ROOT)]
        files += [binary, artifact_ref(work / "dictionary/english.dic", ROOT), artifact_ref(work / "models/6m-q4-fp32.tfwc2", ROOT)]
        options = "-c dictionary/english.dic input archive --transformer models/6m-q4-fp32.tfwc2\n-d dictionary/english.dic archive output --transformer models/6m-q4-fp32.tfwc2\nGAMMA_FX2_ARGMAX_ARM=P|K|D|C\n"
        counted = [(row["path"], row["bytes"]) for row in files] + [("required-option-text", len(options.encode()))]
        package = {"counted_files": files, "option_text": options,
                   "counted_bytes": sum(size for _, size in counted), "dependency_closure_complete": False,
                   "source_runtime_overlap_counted_twice": True, "dependency_closure_failure_reasons": read(PARENT / "package.json")["unresolved"]}
        if package["counted_bytes"] > 10000000:
            raise RuntimeError("raw source/runtime inventory ceiling exceeded")
        atomic_write_json(RESULT / "package.json", package)
        stage["native_binary"] = binary
        source = work / "prof_input/input"
        parent_archive = (PARENT / "work/fixture.cmix").read_bytes()
        negative = []
        for i, invalid in enumerate(("", "DD", "d", "X")):
            name = "invalid-arm-" + str(i)
            record = execute(name, [str(work / "cmix"), "-c", "dictionary/english.dic", "prof_input/input",
                                    name + ".cmix", "--transformer", "models/6m-q4-fp32.tfwc2"],
                             work, 30, {"GAMMA_FX2_ARGMAX_ARM": invalid}, 125)
            if b"Gamma argmax arm must be P, K, D or C" not in (RESULT / (name + ".stderr")).read_bytes():
                raise ValueError("invalid arm did not produce its named failure")
            negative.append(record)
        atomic_write_json(RESULT / "activation-controls.json", {"invalid_arms_rejected": True, "executions": negative})
        for arm in ARMS:
            codec = NativeCodec(work, arm, binary["sha256"])
            result = driver.run(ID, source, 50051, True, run_purpose="diagnostic", run_scope_label=arm + "-public-fixture",
                                run_context="same native binary argmax comparison", run_source="canonical-tool",
                                module=codec, artifact_dir=RESULT / arm, package_inventory=(counted, package))
            for phase in ("encode", "decode", "reencode"):
                compare_trace(work / "P-encode.trace", work / (arm + "-" + phase + ".trace"))
            if not result["roundtrip_ok"] or not result["determinism"]["single_host_byte_equal"]:
                raise ValueError(arm + " inverse or repeat failed")
            if (RESULT / arm / "archive.bin").read_bytes() != parent_archive:
                raise ValueError(arm + " archive differs from retained original parent")
            stage["arms"][arm] = {"result": artifact_ref(RESULT / arm / "result.json", ROOT),
                                  "roundtrip_ok": True, "deterministic_ok": True, "original_parent_archive_identity": True}
        traces = [compare_trace(work / "P-encode.trace", work / (arm + "-" + phase + ".trace"))
                  for arm in ARMS for phase in ("encode", "decode", "reencode")]
        atomic_write_json(RESULT / "coder-records.json", {"record_bytes": 28, "records_per_phase": MODELED_BYTES * 8,
                          "same_native_binary": binary, "all_exact": True, "comparisons": traces,
                          "raw_trace_retention": "Retained locally; exact comparisons, full hashes and block hashes are published. On any mismatch publish first-divergence context."})
        timing = []
        for i, arm in enumerate(TIMING_ORDER):
            name = f"timing-{i}-{arm}"
            codec = NativeCodec(work, arm, binary["sha256"])
            record = codec.invoke(name, ["-c", "dictionary/english.dic", "prof_input/input", name + ".cmix", "--transformer", "models/6m-q4-fp32.tfwc2"], False)
            if (work / (name + ".cmix")).read_bytes() != parent_archive:
                raise ValueError("trace-disabled archive differs")
            timing.append({"arm": arm, "trace_enabled": False, "archive": artifact_ref(work / (name + ".cmix"), ROOT), **record})
        atomic_write_json(RESULT / "timing.json", {"order": TIMING_ORDER, "measurements": timing, "authority": "shared-host diagnostic; two observations per arm do not qualify runtime"})
        verify_inputs()
        if sha(work / "cmix") != binary["sha256"]:
            raise ValueError("native binary changed after comparison")
        stage.update({"status": "passed", "same_binary_all_arms": True, "coder_records_identical": True,
                      "all_archives_match_original_parent": True, "Gamma_archive_gain_bytes": 0})
    except Exception as error:
        stage.update({"status": "execution_failed", "error": type(error).__name__ + ": " + str(error)})
        # A failed native phase can exit before driver artifacts are published.
        # Preserve the first available coder mismatch without replacing its
        # already recorded failure or fabricating absent diagnostics.
        if not (RESULT / "first-divergence.json").exists():
            try:
                reference = RESULT / "work/P-encode.trace"
                if reference.is_file():
                    for target in sorted((RESULT / "work").glob("*.trace")):
                        compare_trace(reference, target)
            except Exception as diagnostic_error:
                stage["failure_trace_diagnostic"] = str(diagnostic_error)
    atomic_write_json(RESULT / "stage-decision.json", stage)
    return 0 if stage["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
