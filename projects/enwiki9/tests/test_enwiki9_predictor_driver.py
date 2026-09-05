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
            for artifact in json.loads(result.read_text())["artifacts"].values():
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
