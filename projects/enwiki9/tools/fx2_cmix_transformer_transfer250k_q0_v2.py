#!/usr/bin/env python3
"""Frozen transfer diagnostic using the measured FX2 binary and existing driver."""
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
ID = "fx2_cmix_transformer_transfer250k_q0_v2"
RESULT = ROOT / "results" / ID
CONTRACT = ROOT / "operations/adaptive/experiments" / (ID + ".json")
PARENT = ROOT / "results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1"
POPULATIONS = (
    ("opening", 0, "665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3"),
    ("distant", 500000000, "f0d01801279f29e353d1dd932a43133e191ea905da6626575b1ee174957717b8"),
)


def sha(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def verify_inputs() -> dict:
    contract = json.loads(CONTRACT.read_text())
    for row in contract["inputs"]:
        path = ROOT / row["path"]
        if (path.is_symlink() and row["id"] != "corpus") or sha(path) != row["sha256"].removeprefix("sha256:"):
            raise ValueError("frozen input changed: " + row["path"])
    return contract


def marker(phase: str, event: str) -> None:
    with Path(os.environ["GAMMA_RESOURCE_PHASE_MARKERS"]).open("a") as handle:
        handle.write(json.dumps({"phase": phase, "event": event}) + "\n")


class NativeCodec:
    """Each driver call executes a fresh, hash-checked native codec process."""

    def __init__(self, work: Path, name: str, binary_sha: str):
        self.work, self.name, self.binary_sha = work, name, binary_sha
        self.encodes = 0
        self.commands = []

    def execute(self, phase: str, arguments: list[str], cap: int = 180) -> None:
        from lib.artifacts import atomic_write_json
        binary = self.work / "cmix"
        if sha(binary) != self.binary_sha:
            raise ValueError("cached executable changed")
        key = self.name + "-" + phase
        command = ["/usr/bin/timeout", "--signal=TERM", "--kill-after=5", str(cap), str(binary), *arguments]
        marker(key, "start")
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        start = time.monotonic()
        with (RESULT / (key + ".stdout")).open("xb") as out, (RESULT / (key + ".stderr")).open("xb") as err:
            done = subprocess.run(command, cwd=self.work, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"}, stdout=out, stderr=err)
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        execution = {"phase": key, "command": command, "returncode": done.returncode,
                     "elapsed_seconds": time.monotonic() - start, "elapsed_cap_seconds": cap,
                     "user_cpu_seconds": after.ru_utime - before.ru_utime,
                     "system_cpu_seconds": after.ru_stime - before.ru_stime,
                     "timing_authority": "shared-host diagnostic"}
        atomic_write_json(RESULT / (key + ".execution.json"), execution)
        self.commands.append(execution)
        marker(key, "end")
        if done.returncode:
            raise RuntimeError(key + " exited " + str(done.returncode))

    def compress(self, raw: bytes) -> bytes:
        phase = "encode" if self.encodes == 0 else "reencode"
        self.encodes += 1
        source = self.work / (self.name + "-" + phase + ".raw")
        target = self.work / (self.name + "-" + phase + ".cmix")
        source.write_bytes(raw)
        self.execute(phase, ["-c", "english.dic", source.name, target.name, "--transformer", "weights.tfwc2"])
        return target.read_bytes()

    def decompress(self, archive: bytes) -> bytes:
        source = self.work / (self.name + "-decode.cmix")
        target = self.work / (self.name + "-decoded.raw")
        source.write_bytes(archive)
        self.execute("decode", ["-d", "english.dic", source.name, target.name, "--transformer", "weights.tfwc2"])
        return target.read_bytes()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    contract = verify_inputs()
    if args.validate_only:
        print(json.dumps({"frozen_inputs_verified": len(contract["inputs"]), "codec_executed": False}))
        return 0
    if os.sched_getaffinity(0) != {2}:
        raise RuntimeError("the launcher must already be pinned to CPU2")
    if not RESULT.is_dir() or any(RESULT.iterdir()):
        raise RuntimeError("canonical executor must create an empty candidate result directory")
    sys.path.insert(0, str(ROOT))
    from lib import driver
    from lib.artifacts import artifact_ref, atomic_write_json

    work = RESULT / "work"
    work.mkdir()
    cached = json.loads((PARENT / "package.json").read_text())
    names = ("cmix", "english.dic", "weights.tfwc2")
    for row, name in zip(cached["runtime_members"], names, strict=True):
        source = ROOT / row["path"]
        if sha(source) != row["sha256"]:
            raise ValueError("measured parent runtime changed")
        shutil.copyfile(source, work / name)
        (work / name).chmod(0o555 if name == "cmix" else 0o444)
        if sha(work / name) != row["sha256"]:
            raise ValueError("runtime copy differs")
    vocabulary = json.loads((ROOT / "operations/provenance/public_fx2_authenticated_vocabulary_20260905.json").read_text())
    allowed = set(vocabulary["vocabulary_bytes"])
    # Keep the parent's conservative source/runtime inventory and count this
    # experiment's exact option text; neither is a complete submission closure.
    option_text = "-c english.dic input archive --transformer weights.tfwc2\n-d english.dic archive output --transformer weights.tfwc2\n"
    counted = [("runtime:" + row["path"], row["bytes"]) for row in cached["runtime_members"]]
    counted += [("source:" + row["path"], row["bytes"]) for row in cached["source_members"]]
    counted.append(("required-option-text", len(option_text.encode())))
    package = {"accounting_class": "conservative-local-source-runtime-inventory", "counted_files": cached["runtime_members"] + cached["source_members"],
               "option_text": option_text, "dependency_closure_complete": False,
               "dependency_closure_failure_reasons": cached["unresolved"], "source_runtime_overlap_counted_twice": True}
    if sum(size for _, size in counted) > 10000000:
        raise RuntimeError("frozen local package ceiling exceeded")
    atomic_write_json(RESULT / "package.json", {**package, "counted_bytes": sum(size for _, size in counted)})
    stage = {"schema": "gamma.enwiki9.fx2-transfer-diagnostic.v1", "candidate_id": ID,
             "status": "running", "populations": [], "scope_bytes": 500000,
             "objective_credit_bytes": 0, "larger_gate_authorized": False,
             "frontend_identity": "gamma-public-fx2-literal-first-block-v1",
             "continuous_guard_decision": "pending outer canonical guard closure"}
    try:
        for name, offset, expected_sha in POPULATIONS:
            with (ROOT / "data/enwik9").open("rb") as handle:
                handle.seek(offset)
                raw = handle.read(250000)
            if len(raw) != 250000 or hashlib.sha256(raw).hexdigest() != expected_sha:
                raise ValueError("frozen raw population changed")
            source = work / (name + ".raw")
            source.write_bytes(raw)
            codec = NativeCodec(work, name, cached["runtime_members"][0]["sha256"])
            stored = work / (name + ".stored")
            codec.execute("preprocess", ["-s", "english.dic", source.name, stored.name], 30)
            storage = stored.read_bytes()
            if storage[:5] != b"\x80\x00\x00\x00\x00":
                raise ValueError("unexpected storage header")
            payload = storage[5:]
            bad = [(i, value) for i, value in enumerate(payload[5:], 5) if value not in allowed]
            compatible = len(payload) >= 10005 and payload[0] == 7 and not bad
            row = {"name": name, "raw_offset": offset, "input": artifact_ref(source, ROOT),
                   "stored": artifact_ref(stored, ROOT), "preprocessed_bytes": len(payload),
                   "modeled_bytes": len(payload) - 5, "mapping_gate_pass": compatible,
                   "first_block_header_hex": payload[:5].hex(), "out_of_alphabet_count": len(bad),
                   "first_out_of_alphabet_positions": bad[:16], "commands": codec.commands}
            stage["populations"].append(row)
            if not compatible:
                stage["status"] = "mapping_rejected"
                break
            result = driver.run(ID, source, 250000, check_determinism=True,
                                run_purpose="diagnostic", run_scope_label=name + "-250k",
                                run_context="unchanged public FX2 parent transfer", run_source="canonical-tool",
                                module=codec, artifact_dir=RESULT / name, package_inventory=(counted, package))
            header = (RESULT / name / "archive.bin").read_bytes()[:46]
            if (header[:4] != b"GFV1" or header[4:9] != payload[:5]
                    or header[14:46].hex() != vocabulary["vocabulary_bitmap_hex"]
                    or not header[9] & 128
                    or (int.from_bytes(header[9:14], "big") & ((1 << 39) - 1)) != len(payload) - 5):
                raise ValueError("native archive framing, length or vocabulary differs")
            row.update({"driver_result": artifact_ref(RESULT / name / "result.json", ROOT),
                        "archive_bytes": result["compressed_size"], "roundtrip_ok": result["roundtrip_ok"],
                        "deterministic_ok": result["determinism"]["single_host_byte_equal"],
                        "archive_header_verified": True})
            if not row["roundtrip_ok"] or not row["deterministic_ok"]:
                stage["status"] = "codec_failed"
                break
        else:
            stage["status"] = "passed"
    except Exception as error:
        stage["status"] = "execution_failed"
        stage["error"] = type(error).__name__ + ": " + str(error)
    atomic_write_json(RESULT / "stage-decision.json", stage)
    return 0 if stage["status"] in {"passed", "mapping_rejected"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
