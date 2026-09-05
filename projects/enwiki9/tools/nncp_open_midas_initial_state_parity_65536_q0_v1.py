"""Compare the sealed open MIDAS loader with the exact raw initialization state."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tarfile
import time

import nncp_libnc_profile_initial_fixture_65536_q0 as raw

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_midas_initial_state_parity_65536_q0_v1"
INITIALIZER_ID = "nncp_libnc_profile_initial_fixture_65536_closurefix_q0_v1"
CORE = ROOT / "programs/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2"
CORE_TREE = "sha256:cc0c7f3c292ee97eac4acea145fb5086247411bcc08f098980c7c312e4fb8789"
CPP = Path(__file__).with_suffix(".cpp")
OBJECTIVE = ROOT / "contracts/research/v2/objective-contract.json"
LIBRARY_SOURCES = (
    "adam_update.cpp", "midpoint_segment.cpp", "midpoint_kernels.cpp",
    "transformer_backward.cpp", "profile_backward.cpp", "profile_artifacts.cpp",
    "profile_compare.cpp", "profile_forward.cpp", "profile_output_head.cpp",
    "profile_population.cpp", "profile_state.cpp", "profile_trace.cpp",
    "tensor_container.cpp", "profile_fixture.cpp")
FLAGS = ("-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror", "-mavx2", "-mfma",
         "-fno-fast-math", "-ffp-contract=off")
FIXTURE_FILES = {
    "parameters": "parameters_initial.coefs", "optimizer": "optimizer_initial.params",
    "state": "state_initial.params", "symbols": "symbols_65536.be16"}
INITIAL_OPTIMIZER_CONFIGURATION = b"gamma.nncp.production.initial.optimizer.v1"
CONSUMER_OPTIMIZER_CONFIGURATION = b"gamma.nncp.production.update.optimizer.v1"


def write_json(path: Path, value: object) -> None:
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def source_files() -> list[Path]:
    return sorted({*raw.local_source_closure((Path(__file__),)), CPP, OBJECTIVE,
                   *(CORE / name for name in LIBRARY_SOURCES), *CORE.glob("*.hpp"),
                   CORE / "CMakeLists.txt", ROOT / "tests/fixtures/enwiki9_release_canary/package/LICENSE"})


def canonical_parameter_names() -> list[str]:
    names = ["embed_out"]
    for layer in reversed(range(20)):
        names += [f"ff2_{layer}", f"ff1_{layer}", f"ln_g_{2 * layer + 1}",
                  f"ln_b_{2 * layer + 1}", f"ff_bias1_{layer}", f"ff_bias2_{layer}",
                  f"w_o_{layer}", f"w_r_{layer}"]
        if layer == 0:
            names.append("b_r_0")
        names += [f"w_kv_{layer}", f"w_q_{layer}", f"ln_g_{2 * layer}", f"ln_b_{2 * layer}"]
    names += ["embed", "ln_g_40", "ln_b_40", "out_bias"]
    if len(names) != 246 or set(names) != set(raw.expected_parameter_layout()):
        raise ValueError("independent canonical parameter population differs")
    return names


def adapt_optimizer_header(source: Path, destination: Path) -> dict:
    """Adapt the configuration tag while retaining the exact tensor body."""
    with source.open("rb") as original, destination.open("xb") as adapted:
        magic, length = struct.unpack("<II", original.read(8))
        if magic != 0x23F4AEFB or length != len(INITIAL_OPTIMIZER_CONFIGURATION):
            raise ValueError("initial optimizer header geometry differs")
        configuration = original.read(length)
        if configuration != INITIAL_OPTIMIZER_CONFIGURATION:
            raise ValueError("initial optimizer configuration differs")
        adapted.write(struct.pack("<II", magic, len(CONSUMER_OPTIMIZER_CONFIGURATION)))
        adapted.write(CONSUMER_OPTIMIZER_CONFIGURATION)
        shutil.copyfileobj(original, adapted, 1024 * 1024)
    def body_hash(path: Path, header_bytes: int) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            stream.seek(header_bytes)
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    original_body = body_hash(source, 8 + len(INITIAL_OPTIMIZER_CONFIGURATION))
    adapted_body = body_hash(destination, 8 + len(CONSUMER_OPTIMIZER_CONFIGURATION))
    if (original_body != adapted_body or destination.stat().st_size - source.stat().st_size
            != len(CONSUMER_OPTIMIZER_CONFIGURATION) - len(INITIAL_OPTIMIZER_CONFIGURATION)):
        raise ValueError("optimizer descriptor/payload body changed during header adaptation")
    return {"source": raw.reference(source), "adapted": raw.reference(destination),
            "sourceConfiguration": INITIAL_OPTIMIZER_CONFIGURATION.decode(),
            "adaptedConfiguration": CONSUMER_OPTIMIZER_CONFIGURATION.decode(),
            "sourceBodySha256": original_body, "adaptedBodySha256": adapted_body,
            "tensorDescriptorAndPayloadBodyIdentical": True,
            "adaptedBytes": destination.stat().st_size}


def reference_state(fixture: Path) -> dict:
    """Hash raw tensor bytes with hashlib, independently of the C++ loader/SHA."""
    digest = hashlib.sha256()
    def u64(value: int) -> None:
        digest.update(struct.pack("<Q", value))
    def string(value: str) -> None:
        encoded = value.encode("utf-8")
        u64(len(encoded))
        digest.update(encoded)
    def vector(container, name: str) -> None:
        record = container.records[name]
        u64(record.byte_count // raw.TYPE_SIZES[record.item_type])
        for offset in range(record.offset, record.offset + record.byte_count, 1024 * 1024):
            digest.update(container._mapping[offset:min(offset + 1024 * 1024,
                                                        record.offset + record.byte_count)])
    names = canonical_parameter_names()
    layout = raw.expected_parameter_layout()
    with (raw.TensorContainer(fixture / FIXTURE_FILES["parameters"]) as parameters,
          raw.TensorContainer(fixture / FIXTURE_FILES["optimizer"]) as optimizer,
          raw.TensorContainer(fixture / FIXTURE_FILES["state"]) as state):
        string("gamma.enwiki9.nncp-profile-future-state.v1")
        for value in (64, 32, 8, 128, 256, 3072, 20, 16392, 0, 64, 1, len(names)):
            u64(value)
        for index, name in enumerate(names):
            item_type, dimensions = layout[name]
            u64(index)
            string(name)
            u64(item_type)
            u64(len(dimensions))
            for value in dimensions:
                u64(value)
            vector(parameters, name)
            if item_type == 1:
                vector(optimizer, name + ".low")
            vector(optimizer, name + ".grad_v")
        u64(20)
        for layer in range(20):
            u64(layer)
            vector(state, f"mem_h_{layer}")
        input_digest = hashlib.sha256(state.payload("input_all_streams")).hexdigest()
        target_digest = hashlib.sha256(state.payload("target_all_streams")).hexdigest()
    return {"futureStateSha256": digest.hexdigest(), "inputBatchSha256": input_digest,
            "targetBatchSha256": target_digest, "parameterTensors": 246, "optimizerTensors": 246,
            "memoryTensors": 20, "nextUpdateExponent": 1, "populationSymbols": 65536,
            "batchSymbols": 2048, "forwardCalls": 0, "gradientCalls": 0,
            "updateCalls": 0, "codedSymbols": 0, "objectiveCreditBytes": 0}


def verified_inputs(experiment: dict) -> dict[str, Path]:
    paths = {}
    for item in experiment["inputs"]:
        path = ROOT / item["path"]
        if (path.is_symlink() or not path.resolve().is_relative_to(ROOT)
                or raw.reference(path, item["id"]) != item):
            raise ValueError(f"frozen input changed: {item['id']}")
        paths[item["id"]] = path
    declared = {item["path"] for item in experiment["inputs"]}
    if any(str(path.relative_to(ROOT)) not in declared for path in source_files()):
        raise ValueError("runtime source closure is not completely declared")
    revision = json.loads(paths["consumer-revision"].read_text())
    if revision["candidateTreeSha256"] != CORE_TREE:
        raise ValueError("sealed consumer source identity differs")
    return paths


def run(command: list[str], log: Path, scratch: Path) -> dict:
    environment = dict(os.environ, TMPDIR=str(scratch))
    start = time.monotonic()
    with log.open("xb") as stream:
        completed = subprocess.run(command, cwd=ROOT, env=environment,
                                   stdout=stream, stderr=subprocess.STDOUT, timeout=600)
    record = {"command": command, "returncode": completed.returncode,
              "elapsedSeconds": time.monotonic() - start, "log": raw.reference(log)}
    if completed.returncode != 0:
        raise RuntimeError(f"bounded parity subprocess failed; see {log}")
    return record


def source_package(destination: Path) -> int:
    tar_path = destination.with_suffix("")
    with tarfile.open(tar_path, "x") as archive:
        for path in source_files():
            info = archive.gettarinfo(str(path), arcname=str(path.relative_to(ROOT)))
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = ""
            info.mode = 0o644
            with path.open("rb") as source:
                archive.addfile(info, source)
    with destination.open("xb") as output:
        output.write(lzma.compress(tar_path.read_bytes(), preset=6))
    tar_path.unlink()
    return destination.stat().st_size


def production(experiment_path: Path, output: Path) -> int:
    experiment_path = experiment_path.resolve()
    output = output.resolve()
    experiment = json.loads(experiment_path.read_text())
    candidate = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if (experiment.get("experimentId") != CANDIDATE_ID or experiment.get("proposalId") != CANDIDATE_ID
            or experiment.get("status") != "frozen" or experiment.get("registrationTiming") != "prospective"
            or experiment.get("evidenceClass") != "oracle" or experiment.get("objectiveCreditBytes") != 0
            or candidate.get("candidateId") != CANDIDATE_ID
            or raw.reference(experiment_path) != json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"])):
        raise ValueError("canonical job and prospective parity contract differ")
    root = ROOT / "results" / CANDIDATE_ID
    if output != root / "decision.json" or not root.is_dir() or any(root.iterdir()):
        raise ValueError("canonical result root must be precreated and empty")
    inputs = verified_inputs(experiment)
    initializer = json.loads(inputs["initializer-decision"].read_text())
    manifest = json.loads(inputs["initializer-manifest"].read_text())
    if (initializer.get("candidateId") != INITIALIZER_ID or initializer.get("promotionPass") is not True
            or initializer.get("decision") != "authorize-successor" or initializer.get("objectiveCreditBytes") != 0
            or manifest["fixture"] != manifest["repeatFixture"]):
        raise ValueError("exact initialization antecedent is absent")
    fixture = ROOT / "results" / INITIALIZER_ID / "fixture"
    if manifest["rawFixturePath"] != str(fixture.relative_to(ROOT)):
        raise ValueError("initializer fixture path differs")
    for role, name in FIXTURE_FILES.items():
        if inputs["fixture-" + role] != fixture / name:
            raise ValueError("actual fixture role or namespace differs")
    symbols = [value[0] for value in struct.iter_unpack(
        ">H", inputs["fixture-symbols"].read_bytes())]
    raw.validate_fixture(fixture, symbols)
    expected = reference_state(fixture)
    write_json(root / "reference-witness.json", expected)
    scratch = root / "work"
    scratch.mkdir()
    adapted_optimizer = scratch / "optimizer-compat.params"
    adaptation = adapt_optimizer_header(inputs["fixture-optimizer"], adapted_optimizer)
    write_json(root / "optimizer-adaptation.json", adaptation)
    compiler = Path(shutil.which("g++") or "/nonexistent").resolve(strict=True)
    executable = scratch / "initial-state-parity"
    command = [str(compiler), *FLAGS, "-I", str(CORE), str(CPP),
               *(str(CORE / name) for name in LIBRARY_SOURCES), "-o", str(executable)]
    executions = [run(command, root / "build.log", scratch)]
    witnesses = []
    for name in ("first", "repeat"):
        witness = root / f"{name}-witness.json"
        command = [str(executable), str(inputs["fixture-parameters"]), str(adapted_optimizer),
                   str(inputs["fixture-state"]), str(inputs["fixture-symbols"]), str(witness)]
        executions.append(run(command, root / f"{name}.log", scratch))
        observed = json.loads(witness.read_text())
        if observed.pop("schema") != "gamma.enwiki9.open-midas-initial-state-witness.v1":
            raise ValueError("unexpected consumer witness schema")
        witnesses.append(observed)
    verified_inputs(experiment)
    write_json(root / "execution.json", {"runs": executions, "compiler": str(compiler),
                                        "compilerSha256": raw.sha256(compiler),
                                        "executableSha256": raw.sha256(executable)})
    source_bytes = source_package(root / "incremental_source.tar.xz")
    measurements = {"initializerPass": True, "consumerSourceExact": True,
                    "rawFixtureBound": True, "freshProcessCount": 2,
                    "optimizerHeaderOnlyAdaptation": True,
                    "adaptedOptimizerBytes": adaptation["adaptedBytes"],
                    "fullStateParity": all(w["futureStateSha256"] == expected["futureStateSha256"] for w in witnesses),
                    "inputBatchParity": all(w["inputBatchSha256"] == expected["inputBatchSha256"] for w in witnesses),
                    "targetBatchParity": all(w["targetBatchSha256"] == expected["targetBatchSha256"] for w in witnesses),
                    "freshProcessRepeat": witnesses[0] == witnesses[1],
                    "completeWitnessParity": all(w == expected for w in witnesses),
                    "populationSymbols": 65536, "parameterTensors": 246,
                    "optimizerTensors": 246, "memoryTensors": 20,
                    "forwardCalls": 0, "gradientCalls": 0, "updateCalls": 0,
                    "codedSymbols": 0, "sourceClosureBytes": source_bytes}
    promotion = raw.evaluate(experiment["promotionPredicates"], measurements)
    kill = raw.evaluate(experiment["killPredicates"], measurements)
    passed = all(row["passed"] for row in promotion)
    killed = all(row["passed"] for row in kill)
    artifacts = [raw.reference(root / name, role) for role, name in (
        ("reference-witness", "reference-witness.json"), ("first-witness", "first-witness.json"),
        ("repeat-witness", "repeat-witness.json"), ("execution", "execution.json"),
        ("optimizer-adaptation", "optimizer-adaptation.json"),
        ("source-package", "incremental_source.tar.xz"))]
    write_json(output, {"schema": "gamma.enwiki9.adaptive-experiment-result.v1",
                        "objective": experiment["objective"], "experiment": raw.reference(experiment_path),
                        "candidateId": CANDIDATE_ID, "candidateRevision": candidate,
                        "evidenceClass": "oracle", "objectiveCreditBytes": 0,
                        "measurements": measurements, "promotionPredicates": promotion,
                        "killPredicates": kill, "promotionPass": passed, "killPass": killed,
                        "decision": "authorize-successor" if passed else "retire" if killed else "retry",
                        "artifacts": artifacts, "generatedUtc": dt.datetime.now(dt.timezone.utc).isoformat()})
    return 0 if passed else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(production(args.experiment, args.output))
