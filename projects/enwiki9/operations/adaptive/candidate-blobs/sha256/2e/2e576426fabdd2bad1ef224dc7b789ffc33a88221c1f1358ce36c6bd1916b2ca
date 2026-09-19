"""Bounded causal predictor and same-build comparison regressions (no dependencies)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
from predictor import CountingPredictor, Frontend, RAW_MSB, TraceIdentity, decode, encode
import driver


class PredictorTests(unittest.TestCase):
    def test_predict_before_truth_and_future_independence(self):
        left, right = CountingPredictor(4), CountingPredictor(4)
        with self.assertRaisesRegex(ValueError, "precede"):
            left.update(1)
        for bit in (0, 1, 1, 0):
            self.assertEqual(left.predict(), right.predict())
            with self.assertRaisesRegex(ValueError, "before predicting"):
                left.predict()
            left.update(bit); right.update(bit)
        self.assertEqual(left.predict(), right.predict())
        left.update(0); right.update(1)
        self.assertNotEqual(left.state_digest(), right.state_digest())

    def test_serialization_preserves_pending_update(self):
        first = CountingPredictor(3)
        first.predict(); first.update(1); first.predict()
        second = CountingPredictor.restore(first.serialize())
        self.assertEqual(first.state_digest(), second.state_digest())
        for model in (first, second):
            with self.assertRaises(ValueError):
                model.predict()
            model.update(0)
        self.assertEqual(first.serialize(), second.serialize())

    def test_frontends_and_trace_cache_are_not_interchangeable(self):
        other = Frontend("WRT-bytes", 1, "coder-event", "msb-first")
        with self.assertRaisesRegex(ValueError, "adapter"):
            CountingPredictor.restore(CountingPredictor().serialize(), other)
        with self.assertRaisesRegex(ValueError, "adapter"):
            encode(b"x", CountingPredictor(frontend=other))
        identity = TraceIdentity(RAW_MSB, "source", "state", "input", 0)
        identity.require(identity)
        with self.assertRaisesRegex(ValueError, "trace reuse"):
            identity.require(TraceIdentity(RAW_MSB, "source", "other-state", "input", 0))

    def test_encoder_decoder_probability_and_state_agreement(self):
        class Recording(CountingPredictor):
            def __init__(self):
                super().__init__(4)
                self.probabilities = []
            def _predict(self):
                p = super()._predict()
                self.probabilities.append(p)
                return p
        rng = random.Random(13)
        for raw in (b"", b"\x00" * 4096, b"\xff" * 4096, bytes(range(256)) * 4,
                    bytes(rng.randrange(256) for _ in range(2048))):
            encoder, decoder = Recording(), Recording()
            archive = encode(raw, encoder)
            self.assertEqual(decode(archive, decoder), raw)
            self.assertEqual(encoder.probabilities, decoder.probabilities)
            self.assertEqual(encoder.state_digest(), decoder.state_digest())
            self.assertEqual(encode(raw, Recording()), archive)
        with self.assertRaisesRegex(ValueError, "budget"):
            decode(b"GPI1" + (1_000_001).to_bytes(8, "big") + b"\0" * 5, Recording())


class DriverTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="enwiki9-driver-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.program = self.root / "program"
        self.program.mkdir()
        (self.program / "meta.json").write_text('{"deps":[]}')
        (self.program / "program.py").write_text(
            'import zlib\n'
            'def compress(raw): return zlib.compress(raw, 1)\n'
            'def decompress(archive): return zlib.decompress(archive)\n'
            'def compress_arm(raw, arm): return zlib.compress(raw, 9 if arm == "T" else 1)\n'
            'def decompress_arm(archive, arm): return zlib.decompress(archive)\n'
            'def stats(): raise OSError("optional telemetry unavailable")\n')
        self.raw = self.root / "data"
        self.raw.write_bytes(b"causal fixture\n" * 1000)
        self.path_patch = patch.object(driver, "_candidate_program_dir", return_value=self.program)
        self.path_patch.start(); self.addCleanup(self.path_patch.stop)
        self.spec = dict(hypothesis="fixture only", parent="zlib1", changed_mechanism="level",
                         development_budget={"configurations": 1}, selection_population="synthetic",
                         sealed_confirmation="none; fixture only", stop_rule="one comparison",
                         arms={"parent": "P", "bookkeeping": "K", "treatment": "T", "control": "C"})

    def test_optional_telemetry_is_missing_not_codec_failure(self):
        with patch.object(driver, "_sample_rss_kib", side_effect=OSError("no proc")):
            result = driver.run("fixture", self.raw, 1024, True)
        self.assertTrue(result["roundtrip_ok"])
        self.assertTrue(result["determinism"]["single_host_byte_equal"])
        self.assertEqual({x["name"] for x in result["missing_diagnostics"]}, {"rss", "program_stats"})
        self.assertFalse(result["resource_evidence_complete"])

    def test_atomic_decision_binds_closed_arm_artifacts_and_rejects_replacement(self):
        output = self.root / "comparison"
        decision = driver.compare("fixture", self.raw, 1024, self.spec, output)
        self.assertTrue(decision["exact_roundtrips_and_repeats"])
        self.assertTrue(decision["parent_bookkeeping_identity"])
        for row in decision["arms"].values():
            result = output / row["result"]
            self.assertEqual(hashlib.sha256(result.read_bytes()).hexdigest(), row["result_sha256"])
            arm_result = json.loads(result.read_text())
            self.assertIn("program_stats", {item["name"] for item in arm_result["missing_diagnostics"]})
            self.assertFalse(arm_result["resource_evidence_complete"])
            self.assertEqual(arm_result["phase_execution"]["decode"]["input_sha256"], arm_result["compressed_sha256"])
            self.assertEqual(arm_result["phase_execution"]["encode"]["input_sha256"], arm_result["data_sha256"])
            for artifact in arm_result["artifacts"].values():
                self.assertTrue((result.parent / artifact["path"]).is_file())
        with self.assertRaises(FileExistsError):
            driver.compare("fixture", self.raw, 1024, self.spec, output)

    def test_roundtrip_first_divergence_and_missing_arm_block_decision(self):
        with (self.program / "program.py").open("a") as stream:
            stream.write('def decompress_arm(archive, arm):\n'
                         ' raw=zlib.decompress(archive)\n'
                         ' return raw[:3]+b"!"+raw[4:] if arm == "T" else raw\n')
        output = self.root / "bad"
        decision = driver.compare("fixture", self.raw, 1024, self.spec, output)
        self.assertEqual(decision["verdict"], "invalid")
        self.assertEqual(json.loads((output / "T/result.json").read_text())["first_divergence_byte"], 3)
        self.assertFalse(decision["promotion_authorized"])

    def test_changed_population_invalidates_comparison(self):
        original = driver.run
        calls = 0
        def change_after_run(*args, **kwargs):
            nonlocal calls
            result = original(*args, **kwargs)
            calls += 1
            if calls == 2:
                self.raw.write_bytes(b"different population" * 100)
            return result
        with patch.object(driver, "run", side_effect=change_after_run):
            decision = driver.compare("fixture", self.raw, 1024, self.spec, self.root / "changed-input")
        self.assertFalse(decision["same_input_population"])
        self.assertEqual(decision["verdict"], "invalid")

    def test_decoder_cannot_reuse_encoder_truth_cache(self):
        with (self.program / "program.py").open("a") as stream:
            stream.write('cached = None\n'
                         'def compress_arm(raw, arm):\n'
                         ' global cached\n'
                         ' cached=raw\n'
                         ' return b"" if arm == "T" else zlib.compress(raw)\n'
                         'def decompress_arm(archive, arm):\n'
                         ' return cached if arm == "T" else zlib.decompress(archive)\n')
        output = self.root / "cached-truth"
        decision = driver.compare("fixture", self.raw, 1024, self.spec, output)
        self.assertEqual(decision["verdict"], "invalid")
        failure = json.loads((output / "T/result.json").read_text())
        self.assertEqual(failure["failed_phase"], "decode")
        self.assertEqual((output / "T/archive.bin").read_bytes(), b"")
        self.assertIn("archive", failure["artifacts"])
        self.assertIn("decode_stderr.log", failure["artifacts"])

    def test_arm_initial_state_is_independent_of_prior_arms(self):
        with (self.program / "program.py").open("a") as stream:
            stream.write('parent_seen=False\n'
                         'def compress_arm(raw, arm):\n'
                         ' global parent_seen\n'
                         ' if arm == "P": parent_seen=True\n'
                         ' return zlib.compress(raw, 9 if arm == "T" and parent_seen else 1)\n')
        output = self.root / "arm-state"
        decision = driver.compare("fixture", self.raw, 1024, self.spec, output)
        self.assertEqual(decision["verdict"], "measured-no-improvement")
        self.assertEqual(decision["treatment_minus_parent_bytes"], 0)
        pids = []
        for row in decision["arms"].values():
            result = json.loads((output / row["result"]).read_text())
            pids.extend(phase["pid"] for phase in result["phase_execution"].values())
        self.assertEqual(len(pids), len(set(pids)))

    def test_archive_replacement_between_arms_invalidates_decision(self):
        output = self.root / "replaced-archive"
        original = driver.run
        calls = 0
        def replace_after_arm(*args, **kwargs):
            nonlocal calls
            result = original(*args, **kwargs)
            calls += 1
            if calls == 2:
                (output / "P/archive.bin").write_bytes(b"replacement")
            return result
        with patch.object(driver, "run", side_effect=replace_after_arm):
            decision = driver.compare("fixture", self.raw, 1024, self.spec, output)
        self.assertEqual(decision["verdict"], "invalid")
        self.assertFalse(decision["artifact_closure_valid"])
        self.assertIn("parent", decision["artifact_validation_errors"])

    def test_result_replacement_between_arms_keeps_original_binding(self):
        output = self.root / "replaced-result"
        original = driver.run
        original_digest = None
        def replace_result(*args, **kwargs):
            nonlocal original_digest
            result = original(*args, **kwargs)
            if kwargs["arm"] == "P":
                path = output / "P/result.json"
                original_digest = hashlib.sha256(path.read_bytes()).hexdigest()
                path.write_text("{}\n")
            return result
        with patch.object(driver, "run", side_effect=replace_result):
            decision = driver.compare("fixture", self.raw, 1024, self.spec, output)
        self.assertEqual(decision["verdict"], "invalid")
        self.assertEqual(decision["arms"]["parent"]["result_sha256"], original_digest)
        self.assertIn("parent", decision["artifact_validation_errors"])

    def test_repeat_failure_retains_first_archive_and_restored_output(self):
        marker = self.root / "encode-count.json"
        with (self.program / "program.py").open("a") as stream:
            stream.write('from pathlib import Path\nimport json\n'
                         f'counts_path=Path({str(marker)!r})\n'
                         'def compress_arm(raw, arm):\n'
                         ' counts=json.loads(counts_path.read_text()) if counts_path.exists() else {}\n'
                         ' counts[arm]=counts.get(arm,0)+1\n'
                         ' counts_path.write_text(json.dumps(counts))\n'
                         ' if counts[arm] == 2: raise ValueError("injected repeat failure")\n'
                         ' return zlib.compress(raw)\n')
        output = self.root / "repeat-failure"
        decision = driver.compare("fixture", self.raw, 1024, self.spec, output)
        self.assertEqual(decision["verdict"], "invalid")
        result = json.loads((output / "P/result.json").read_text())
        self.assertEqual(result["failed_phase"], "repeat")
        self.assertIn("archive", result["artifacts"])
        self.assertIn("restored", result["artifacts"])
        self.assertEqual((output / "P/restored.bin").read_bytes(), self.raw.read_bytes()[:1024])

    def add_local_helper(self):
        helper = self.program / "support.py"
        helper.write_text('import zlib\ndef encode(raw): return zlib.compress(raw)\n')
        with (self.program / "program.py").open("a") as stream:
            stream.write('import support\ndef compress_arm(raw, arm): return support.encode(raw)\n')
        return helper

    def test_live_source_and_helper_substitution_cannot_change_frozen_arms(self):
        helper = self.add_local_helper()
        source = self.program / "program.py"
        originals = {path: path.read_bytes() for path in (source, helper)}
        output = self.root / "frozen-source"
        original_run = driver.run

        def substitute_during_arm(*args, **kwargs):
            if kwargs["arm"] != "K":
                return original_run(*args, **kwargs)
            for path in originals:
                path.write_text('raise ValueError("substituted live source")\n')
            try:
                return original_run(*args, **kwargs)
            finally:
                for path, payload in originals.items():
                    path.write_bytes(payload)

        with patch.object(driver, "run", side_effect=substitute_during_arm):
            decision = driver.compare("fixture", self.raw, 1024, self.spec, output)
        self.assertTrue(decision["same_candidate_build"])
        self.assertEqual(decision["verdict"], "measured-no-improvement")
        manifest = json.loads((output / "build.json").read_text())
        for row in decision["arms"].values():
            result = json.loads((output / row["result"]).read_text())
            for phase in result["phase_execution"].values():
                for path, payload in originals.items():
                    relative = "projects/enwiki9/programs/fixture/" + path.name
                    expected = hashlib.sha256(payload).hexdigest()
                    self.assertEqual(phase["loaded_sources"][relative], expected)
                    self.assertEqual(manifest["files"][relative]["sha256"], expected)

    def test_frozen_helper_substitution_after_parent_check_is_rejected(self):
        self.add_local_helper()
        output = self.root / "frozen-race"
        original_subprocess = driver.subprocess.run
        injected = False

        def substitute_at_child_start(command, **kwargs):
            nonlocal injected
            if injected or command[1:2] != ["-c"]:
                return original_subprocess(command, **kwargs)
            injected = True
            helper = output / "build/projects/enwiki9/programs/fixture/support.py"
            original = helper.read_bytes()
            helper.chmod(0o644)
            helper.write_text('import zlib\ndef encode(raw): return zlib.compress(raw, 9)\n')
            try:
                return original_subprocess(command, **kwargs)
            finally:
                helper.write_bytes(original)
                helper.chmod(0o444)

        with patch.object(driver.subprocess, "run", side_effect=substitute_at_child_start):
            decision = driver.compare("fixture", self.raw, 1024, self.spec, output)
        self.assertTrue(injected)
        self.assertTrue(decision["source_stable"])
        self.assertFalse(decision["same_candidate_build"])
        self.assertEqual(decision["verdict"], "invalid")
        self.assertIn("frozen source bytes changed", decision["errors"]["parent"]["message"])

    def test_missing_loaded_source_receipt_is_mandatory_evidence_failure(self):
        output = self.root / "missing-source-receipt"
        original_subprocess = driver.subprocess.run

        def remove_mandatory_receipt(command, **kwargs):
            result = original_subprocess(command, **kwargs)
            if command[1:2] == ["-c"]:
                Path(command[6]).unlink(missing_ok=True)
            return result

        with patch.object(driver.subprocess, "run", side_effect=remove_mandatory_receipt):
            decision = driver.compare("fixture", self.raw, 1024, self.spec, output)
        self.assertEqual(decision["verdict"], "invalid")
        self.assertFalse(decision["same_candidate_build"])
        result = json.loads((output / "P/result.json").read_text())
        self.assertEqual(result["failed_phase"], "encode")
        self.assertIn("archive", result["artifacts"])

    def test_changed_input_source_is_rejected_while_freezing(self):
        source = self.program / "program.py"
        expected = {str(source): hashlib.sha256(source.read_bytes()).hexdigest()}
        source.write_text('raise ValueError("replacement")\n')
        with self.assertRaisesRegex(ValueError, "source changed while freezing"):
            driver._freeze_comparison_build("fixture", source, self.root / "freeze-race",
                                           source_hashes=expected)



class ObjectiveTests(unittest.TestCase):
    def test_new_target_retains_historical_digest_and_rejects_rebinding(self):
        r = driver.research_contracts
        old = r.objective_binding(objective_path="contracts/research/v1/objective-contract.json")
        self.assertEqual(old["objectiveDigest"], "sha256:ce4c435c0f398caf65a09050c8518d9c5ea63239f9156048ea2aaaf9b8ffa7e8")
        r._validate_objective_binding(old, "historical")
        self.assertEqual(r.objective_binding()["targetScoreBytes"], 99_000_000)
        old["targetScoreBytes"] = 99_000_000
        with self.assertRaisesRegex(ValueError, "immutable objective"):
            r._validate_objective_binding(old, "forged")


if __name__ == "__main__":
    unittest.main()
