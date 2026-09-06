"""Bounded MIDAS runner controls; corpus execution is never part of these tests."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.artifacts import artifact_ref, atomic_write_json
from lib import native_fixture_build_cache as cache
from tools import midas_open_codec_v1 as codec
from tools import midas_open_corpus_gate_v1 as runner

CACHE = ROOT / "results/midas_open_source_bundle_v1_unit_20260906/cache/entries/9e25dbdbbc4e49bcf6ad65fc9d9434276163d5456462381493d038dc2540fb36"
RAW = bytes((17 * i + 3) & 255 for i in range(65))


class Failure(ValueError):
    def __init__(self, category):
        self.category = category
        super().__init__(category)


class FixtureGate:
    def __init__(self, root, raw=RAW, *, real=False):
        self.root = root
        self.result = root / "result"
        self.result.mkdir()
        self.work = self.result / "work"
        self.work.mkdir()
        self.population = self.work / "raw"
        self.population.write_bytes(raw)
        self.raw = raw
        self.binary = self.work / "program"
        self.binary.write_bytes(b"mock binary")
        self.binaries, self.commands, self.required = {}, [], set()
        self.closed = True
        self.real = real
        self.fail_phase = None
        self.mutation = None
        self.sizes = {"P": 7, "K": 7, "F": 6, "S": 8}

    def artifact(self, path):
        return artifact_ref(path, self.root)

    def write(self, name, value):
        atomic_write_json(self.result / name, value)

    def closure(self):
        if not self.closed:
            raise Failure("children_remain")

    def verify(self):
        return None

    def run(self, name, argv, cap, env=None):
        if name == self.fail_phase:
            self.commands.append({"phase": name, "returncode": 124})
            raise Failure("budget_exhausted")
        output = Path(argv[-1])
        operation, arm, limit = argv[1], argv[2], int(argv[3])
        if self.real:
            result = subprocess.run(argv, capture_output=True, timeout=cap,
                                    env={"PATH": os.defpath, "LC_ALL": "C", **(env or {})},
                                    preexec_fn=lambda: os.sched_setaffinity(0, {2}))
            (self.result / (name + ".stdout")).write_bytes(result.stdout)
            (self.result / (name + ".stderr")).write_bytes(result.stderr)
            self.commands.append({"phase": name, "returncode": result.returncode})
            self.write(name + ".execution.json", self.commands[-1])
            if result.returncode:
                raise AssertionError(result.stderr.decode(errors="replace"))
            return self.commands[-1]
        output.mkdir()
        archive = bytes([70 if arm == "F" else 83 if arm == "S" else 80]) * self.sizes[arm]
        data = self.raw if operation == "decode" else archive
        parts = (arm.encode() + b"full", b"parent" if arm in "PK" else arm.encode(), b"coder", b"reference" if arm in "PK" else arm.encode())
        state = b"GMST\x01" + b"".join(len(part).to_bytes(8, "little") + part for part in parts)
        (output / "data").write_bytes(data)
        (output / "state.bin").write_bytes(state)
        n = len(self.raw)
        summary = {"schema": "midas_open_codec_operation_v1", "operation": operation, "arm": arm,
                   "frontend": "raw_identity_v1", "raw_bytes": n, "archive_bytes": len(archive),
                   "max_raw_bytes": limit, "state_bytes": len(state), "objective_credit_bytes": 0,
                   "resource_qualified": False, "model_updates": n // 64 + (n // 64 + (n % 64 >= 32) if arm in "FS" else 0)}
        (output / "summary.json").write_text(json.dumps(summary))
        (self.result / (name + ".stdout")).write_text(json.dumps(summary))
        (self.result / (name + ".stderr")).write_bytes(b"")
        if self.mutation:
            self.mutation(name, output)
        self.commands.append({"phase": name, "returncode": 0})
        self.write(name + ".execution.json", self.commands[-1])
        return self.commands[-1]


class GateTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="gamma-midas-gate-unit-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.gate = FixtureGate(self.root)
        self.built = types.SimpleNamespace(binary=self.gate.binary, cache_hit=True, manifest={})

    def compare(self):
        return runner.compare_arms(self.gate, codec, self.built, self.gate.population, 1)

    def test_all_twelve_phases_and_distinct_success_fields(self):
        result = self.compare()
        self.assertEqual(len(self.gate.commands), 12)
        self.assertEqual(result["scientific_verdict"], "positive_component")
        self.assertTrue(result["all_arm_full_state_identity"])
        self.assertTrue(result["pk_parent_projection_identity"])
        self.assertEqual(result["F_vs_P_archive_saved_bytes"], 1)

    def test_compression_loss_does_not_skip_controls_or_invalidate_infrastructure(self):
        self.gate.sizes.update(F=9, S=10)
        result = self.compare()
        self.assertEqual(len(self.gate.commands), 12)
        self.assertTrue(result["infrastructure_pass"])
        self.assertTrue(result["causal_controls_pass"])
        self.assertFalse(result["compression_positive"])
        self.assertEqual(result["scientific_verdict"], "compression_loss")

    def test_directional_and_pk_controls_are_separate_from_compression(self):
        self.gate.sizes.update(K=8, S=5)
        result = self.compare()
        self.assertTrue(result["compression_positive"])
        self.assertFalse(result["pk_archive_identity"])
        self.assertFalse(result["F_beats_S_archive"])
        self.assertEqual(result["scientific_verdict"], "causal_control_failed")
        self.assertEqual(len(self.gate.commands), 12)

    def test_same_arm_state_mismatch_is_implementation_failure(self):
        def mutation(name, output):
            if name == "P-decode":
                path = output / "state.bin"
                data = bytearray(path.read_bytes()); data[-1] ^= 1; path.write_bytes(data)
        self.gate.mutation = mutation
        with self.assertRaisesRegex(runner.EvidenceFailure, "complete final state") as caught:
            self.compare()
        self.assertEqual(runner.classify(caught.exception), "implementation_or_infrastructure_failure")
        divergence = json.loads((self.gate.result / "first-state-divergence.json").read_bytes())
        self.assertEqual(divergence["comparison"], "P encode/decode")
        self.assertNotEqual(divergence["left_hex"], divergence["right_hex"])

    def test_missing_output_or_false_update_count_fails_closed(self):
        def mutation(name, output):
            if name == "P-encode":
                (output / "state.bin").unlink()
        self.gate.mutation = mutation
        with self.assertRaisesRegex(runner.EvidenceFailure, "output set"):
            self.compare()

    def test_budget_failure_retains_phase_and_classification(self):
        self.gate.fail_phase = "P-decode"
        with self.assertRaises(Failure) as caught:
            self.compare()
        self.assertEqual(runner.classify(caught.exception), "budget_exhausted")
        self.assertEqual(self.gate.commands[-1], {"phase": "P-decode", "returncode": 124})
        self.assertEqual(runner.classify(Failure("resource_or_signal_stop")), "resource_or_signal_stop")
        for code in (137, -9):
            self.assertEqual(runner.classify(Failure("execution_failed"), [{"returncode": code}]), "resource_or_signal_stop")
        for code in (152, 153, -24, -25):
            self.assertEqual(runner.classify(Failure("execution_failed"), [{"returncode": code}]), "budget_exhausted")
        self.assertEqual(runner.classify(Failure("execution_failed"), [{"returncode": 1}]), "implementation_or_infrastructure_failure")

    def test_seeded_cache_miss_or_changed_bytes_never_compiles(self):
        candidate = "unit"
        work = self.root / "results" / candidate / "work"
        entry = work / "cache/entries/key"
        entry.mkdir(parents=True)
        original_manifest = self.root / "original.json"; original_manifest.write_bytes(b"{}\n")
        original_binary = self.root / "original-program"; original_binary.write_bytes(b"program")
        plan = {"candidate_id": candidate, "cached_manifest": artifact_ref(original_manifest, self.root),
                "cached_binary": artifact_ref(original_binary, self.root)}
        (entry / "manifest.json").write_bytes(original_manifest.read_bytes())
        (entry / "program").write_bytes(original_binary.read_bytes())
        manifest = {"key": "key", "identity": {}}
        with patch.object(runner, "ROOT", self.root), patch.object(runner, "verify_build_sources"), \
             patch.object(codec, "build", side_effect=AssertionError("compilation forbidden")) as build, \
             patch.object(cache, "build_cpp_cached", side_effect=AssertionError("compilation forbidden")) as compile_, \
             patch.object(cache, "_cached", return_value=(None, "invalid_manifest")) as validator:
            with self.assertRaisesRegex(runner.EvidenceFailure, "failed validation"):
                runner.seeded_cached_build(codec, {}, plan, manifest)
            (entry / "program").write_bytes(b"changed")
            with self.assertRaisesRegex(runner.EvidenceFailure, "program bytes differ"):
                runner.seeded_cached_build(codec, {}, plan, manifest)
            (entry / "program").unlink()
            with self.assertRaises(FileNotFoundError):
                runner.seeded_cached_build(codec, {}, plan, manifest)
            self.assertEqual(validator.call_count, 1)
            build.assert_not_called(); compile_.assert_not_called()

    def test_changed_population_digest_and_alias_are_rejected(self):
        ref = self.gate.artifact(self.gate.population)
        self.gate.population.write_bytes(b"changed")
        with self.assertRaisesRegex(runner.EvidenceFailure, "reference differs"):
            runner.reference_bytes(self.root, ref)
        link = self.root / "alias"; link.symlink_to(self.gate.population)
        with self.assertRaisesRegex(runner.EvidenceFailure, "aliased"):
            runner.bounded_read(link)
        fifo = self.root / "fifo"; os.mkfifo(fifo)
        with self.assertRaisesRegex(runner.EvidenceFailure, "nonregular"):
            runner.bounded_read(fifo)

    def test_false_model_update_count_is_rejected(self):
        def mutation(name, output):
            if name == "P-encode":
                row = json.loads((output / "summary.json").read_bytes())
                row["model_updates"] += 1
                (output / "summary.json").write_text(json.dumps(row))
                (self.gate.result / (name + ".stdout")).write_text(json.dumps(row))
        self.gate.mutation = mutation
        with self.assertRaisesRegex(runner.EvidenceFailure, "causal update count"):
            self.compare()

    def test_changed_build_source_and_unbound_dependency_are_rejected(self):
        source = self.root / "source.cpp"; source.write_bytes(b"int unit;")
        record = codec.file_record(source)
        identity = {"cwd": str(self.root), "sources": [str(source)], "flags": ["-O2", "-Werror=date-time"],
                    "dependencies": [record], "compiler": {"executable": record, "toolchain_files": []}}
        manifest = {"schema": "gamma.native_fixture_build_cache.v1", "key": runner.digest(runner.canonical(identity)),
                    "identity": identity}
        manifest["manifest_sha256"] = runner.digest(runner.canonical(manifest))
        local_codec = types.SimpleNamespace(SOURCES=[source], FLAGS=("-O2",), file_record=codec.file_record)
        with patch.object(runner, "ROOT", self.root):
            with self.assertRaisesRegex(runner.EvidenceFailure, "lacks an experiment binding"):
                runner.verify_build_sources(local_codec, manifest, {})
            runner.verify_build_sources(local_codec, manifest, {"source.cpp": record})
            source.write_bytes(b"changed")
            with self.assertRaisesRegex(runner.EvidenceFailure, "dependency changed"):
                runner.verify_build_sources(local_codec, manifest, {"source.cpp": record})

    def test_runtime_inventory_drift_is_rejected(self):
        expected = {"runtime": {"missing": [], "files": [{"sha256": "old"}]}, "local_source_files": [],
                    "local_source_bytes": 0, "toolchain_system_dependency_files": 0}
        observed = {**expected, "runtime": {"missing": [], "files": [{"sha256": "new"}]}}
        with self.assertRaisesRegex(runner.EvidenceFailure, "runtime files"):
            runner.verify_inventory(types.SimpleNamespace(inventory=lambda built: observed), None, expected)

    def test_contract_and_output_identities_are_unique(self):
        with self.assertRaisesRegex(runner.EvidenceFailure, "duplicate"):
            runner.contract_inputs({"inputs": [{"id": "x", "path": "one"}, {"id": "x", "path": "two"}]})
        with self.assertRaises(FileExistsError):
            FixtureGate(self.root)
        with self.assertRaisesRegex(runner.EvidenceFailure, "candidate"):
            runner.bound_contract("../arbitrary")

    def test_plan_rejects_unbounded_population_and_zero_wall(self):
        plan = {"schema": runner.PLAN_SCHEMA, "candidate_id": "unit", "population": {"bytes": 65},
                "cached_manifest": {}, "cached_binary": {}, "phase_wall_seconds": 120,
                "resources": {"cpus": [2], "memory_bytes": 2 * 1024**3, "scratch_bytes": 256 * 1024**2,
                              "swap_bytes": 0, "wall_seconds": 1800}}
        runner.validate_plan(plan, "unit")
        plan["phase_wall_seconds"] = 0
        with self.assertRaises(runner.EvidenceFailure):
            runner.validate_plan(plan, "unit")
        plan["phase_wall_seconds"] = 120; plan["population"]["bytes"] = 250001
        with self.assertRaises(runner.EvidenceFailure):
            runner.validate_plan(plan, "unit")

    def test_unclosed_children_publish_failed_decision_without_work_hashes(self):
        self.gate.closed = False
        self.gate.required.add(self.gate.work / "missing")
        stage = {"status": "passed", "infrastructure_pass": True}
        with patch.object(runner, "bounded_read", side_effect=AssertionError("must not hash live work")):
            result = runner.finalize(self.gate, stage, lambda: None)
        self.assertFalse(result["infrastructure_pass"])
        self.assertFalse(result["child_closure_ok"])
        self.assertTrue((self.gate.result / "stage-decision.json").is_file())

    def test_missing_fingerprint_and_index_publication_failure_keep_failed_stage(self):
        self.gate.required.add(self.gate.work / "missing")
        write = self.gate.write
        def fail_index(name, value):
            if name == "artifacts.json":
                raise OSError("fixture publication failure")
            write(name, value)
        self.gate.write = fail_index
        result = runner.finalize(self.gate, {"status": "passed", "infrastructure_pass": True}, lambda: None)
        self.assertFalse(result["infrastructure_pass"])
        self.assertIn("publication failure", json.dumps(result))
        self.assertEqual(json.loads((self.gate.result / "stage-decision.json").read_bytes())["status"], "failed")

    def test_verification_child_must_close_before_indexing(self):
        def verify():
            self.gate.closed = False
            raise OSError("fixture verification child did not close")
        with patch.object(runner, "bounded_read", side_effect=AssertionError("must not hash live work")):
            result = runner.finalize(self.gate, {"status": "passed", "infrastructure_pass": True}, verify)
        self.assertFalse(result["child_closure_ok"])
        self.assertFalse(result["infrastructure_pass"])


class CachedSyntheticReplayTest(unittest.TestCase):
    def test_retained_build_and_runtime_authorities_match_without_build(self):
        if not (CACHE / "manifest.json").is_file():
            self.skipTest("retained cached MIDAS manifest unavailable")
        manifest = json.loads((CACHE / "manifest.json").read_bytes())
        evidence = json.loads((ROOT / runner.EVIDENCE).read_bytes())
        runtime = json.loads((ROOT / runner.RUNTIME_EVIDENCE).read_bytes())["measured_inventory"]
        inputs = {row["path"]: row for row in evidence["source_bindings"] if row["path"] != "../../LICENSE"}
        for row in manifest["identity"]["dependencies"]:
            path = Path(row["path"])
            if path.is_relative_to(ROOT):
                inputs[str(path.relative_to(ROOT))] = row
        runner.verify_build_sources(codec, manifest, inputs)
        built = types.SimpleNamespace(binary=CACHE / "program", cache_hit=True, manifest=manifest)
        observed = runner.verify_inventory(codec, built, runtime)
        self.assertFalse(observed["complete_package_qualified"])
        self.assertEqual(observed["required_trained_model_assets"], [])

    def test_cached_all_arm_65_byte_replay_no_build_or_corpus(self):
        if not (CACHE / "program").is_file() or not (CACHE / "manifest.json").is_file():
            self.skipTest("retained cached MIDAS executable unavailable; this test never compiles")
        if 2 not in os.sched_getaffinity(0):
            self.skipTest("assigned CPU2 unavailable")
        manifest = json.loads((CACHE / "manifest.json").read_bytes())
        self.assertEqual(manifest["binary"], {"bytes": 373384, "sha256": "d44f898b5355bdb85b1869808384b0906b4bff8d18e498fc3621ab5b8103a546"})
        built = types.SimpleNamespace(binary=CACHE / "program", cache_hit=True, manifest=manifest)
        codec.verified_binary(built)
        with tempfile.TemporaryDirectory(prefix="gamma-midas-gate-real65-") as directory:
            gate = FixtureGate(Path(directory), real=True)
            result = runner.compare_arms(gate, codec, built, gate.population, 120)
            known = json.loads((ROOT / "operations/evidence/20260905_midas_open_profile_parent_roundtrip_unit.json").read_bytes())
            for arm in "PKFS":
                archive = (gate.result / arm / "encode/data").read_bytes()
                self.assertEqual(hashlib.sha256(archive).hexdigest(), known["finite_artifacts"]["arms"][arm]["archive_sha256"])
                self.assertEqual(len(archive), 105)
            self.assertEqual(len(gate.commands), 12)
            self.assertTrue(result["infrastructure_pass"])
            self.assertTrue(result["pk_archive_identity"])
            self.assertTrue(result["pk_parent_projection_identity"])
            self.assertTrue(result["all_arm_full_state_identity"])
            self.assertFalse(result["compression_positive"])


if __name__ == "__main__":
    unittest.main()
