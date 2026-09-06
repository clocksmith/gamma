#!/usr/bin/env python3
"""Bounded synthetic falsifiers for prefix causality and exact field coding."""
import hashlib
import json
import os
from pathlib import Path
import random
import resource
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import causal_field_dependency_v1 as codec

OAK = b"Oakford is a town with an exact repeated description."
PINE = b"Pinewell has different facts and a different description."


def record(name, value, suffix=b"}}"):
    return b"{{place|name=" + name + b"|description=" + value + suffix


def fixtures():
    seed = record(b"Oakford", OAK) + record(b"Pinewell", PINE)
    return {"conditional": seed + record(b"Oakford", OAK),
            "malformed": seed + record(b"Oakford", OAK[:7], b"{{nested|name=Oakford|description=poison}}}}")
                + record(b"Oakford", OAK, b"|name=duplicate}}") + b"{{unfinished|name=Oakford|description=",
            "arbitrary": bytes(range(256)) + b"\x00\xff\r\n New  York NEW YORK &#124; {{ spaced |KEY=value=exact|other=\xff\x00}}"}


def feed(model, raw):
    probabilities = []
    for byte in raw:
        for shift in range(7, -1, -1):
            probabilities.append(model.predict())
            model.observe((byte >> shift) & 1)
    return probabilities


def state_blob(row):
    payload = codec.canonical(row)
    return b"CFDS1" + struct.pack("<I", len(payload)) + codec.digest(payload) + payload


class FieldCodecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retained = Path(os.environ["GAMMA_CAUSAL_FIELD_UNIT_RETAIN"]) if os.environ.get("GAMMA_CAUSAL_FIELD_UNIT_RETAIN") else None
        if cls.retained is not None:
            cls.retained.mkdir(exist_ok=False)

    def exact(self, raw, arm):
        archive, encoded = codec.encode(raw, arm)
        restored, decoded = codec.decode(archive, arm)
        repeated, repeat = codec.encode(restored, arm)
        self.assertEqual(restored, raw)
        self.assertEqual(archive, repeated)
        self.assertEqual(encoded, decoded)
        self.assertEqual(encoded, repeat)
        self.assertEqual(len(archive), encoded["header_bytes"] + encoded["payload_bytes"])
        return archive, encoded

    def test_all_arms_exact_on_synthetic_populations(self):
        for name, raw in fixtures().items():
            archives, reports = {}, {}
            for arm in codec.ARMS:
                with self.subTest(fixture=name, arm=arm):
                    archives[arm], reports[arm] = self.exact(raw, arm)
            self.assertEqual(archives["P"], archives["K"])
            self.assertEqual(reports["P"]["probability_digest"], reports["K"]["probability_digest"])
            self.assertEqual(len({reports[arm]["dictionary_digest"] for arm in "KTRS"}), 1)

    def test_three_record_conditional_falsifier(self):
        reports = {arm: self.exact(fixtures()["conditional"], arm)[1] for arm in codec.ARMS}
        self.assertLess(reports["T"]["complete_archive_bytes"], reports["P"]["complete_archive_bytes"])
        self.assertLess(reports["T"]["complete_archive_bytes"], reports["R"]["complete_archive_bytes"])
        self.assertLess(reports["T"]["complete_archive_bytes"], reports["S"]["complete_archive_bytes"])
        self.assertGreater(reports["T"]["specialist_bits"], 0)
        self.assertIsNone(reports["T"]["complete_package_bytes"])
        self.assertFalse(reports["T"]["qualification_authority"])

    def test_future_suffixes_never_change_shared_prefix(self):
        prefix = record(b"Oakford", OAK) + record(b"Pinewell", PINE) + b"{{place|name=Oakford|description=Oakford"
        suffixes = [OAK[7:] + b"}}", b"|name=duplicate}}", b"{{nested|name=Oakford|description=poison}}}}",
                    b"x" * 100 + b"}}", b""]
        for arm in "KTRS":
            baseline = None
            for suffix in suffixes:
                model = codec.Predictor(arm)
                trace = []
                for byte in prefix + suffix:
                    if model.bits // 8 < len(prefix):
                        before = model.bits
                        probabilities = feed(model, bytes([byte]))
                        trace.append((before, probabilities, model.state_digest()))
                    else:
                        feed(model, bytes([byte]))
                if baseline is None:
                    baseline = trace
                self.assertEqual(trace, baseline)
                self.assertEqual(model.completed_invocations, 3 if suffix == suffixes[0] else 2)
                self.assertEqual(model.serial, 3 if suffix == suffixes[0] else 2)

    def test_prefix_parser_never_commits_until_second_close(self):
        model = codec.Predictor()
        raw = record(b"Oakford", OAK)
        for index, byte in enumerate(raw):
            feed(model, bytes([byte]))
            self.assertEqual(len(model.table), 1 if index == len(raw) - 1 else 0)
        self.assertEqual(model.completed_invocations, 1)

    def test_nested_and_overlong_invocations_remain_quarantined(self):
        model = codec.Predictor()
        malicious = b"{{outer|name=Oakford|description=" + b"x" * 2050 + record(b"poison", b"poison") + b"}}"
        feed(model, malicious)
        self.assertFalse(model.table)
        self.assertEqual(model.completed_invocations, 0)
        self.assertEqual(model.rejected_invocations, 1)
        feed(model, record(b"after", b"valid"))
        self.assertEqual(model.completed_invocations, 1)
        self.assertEqual(len(model.table), 1)

    def test_unknown_and_duplicate_keys_do_not_choose_hidden_donors(self):
        for suffix in (b"|name=duplicate}}", b"|description=duplicate}}"):
            model = codec.Predictor()
            feed(model, record(b"Oakford", OAK) + record(b"Oakford", b"poison", suffix))
            self.assertEqual(model.table[(b"place", b"name", b"Oakford", b"description")][0], OAK)
            self.assertEqual(model.completed_invocations, 1)
        model = codec.Predictor()
        feed(model, record(b"Oakford", OAK) + b"{{place|name=Oakford|unseen=")
        self.assertIsNone(model.donor)

    def test_fifo_capacity_and_existing_key_replacement(self):
        model = codec.Predictor()
        for index in range(130):
            feed(model, record(str(index).encode(), b"v"))
        self.assertEqual(len(model.table), 128)
        self.assertEqual(model.evictions, 2)
        first = next(iter(model.table))
        self.assertEqual(first[2], b"2")
        order = list(model.table)
        feed(model, record(b"2", b"replaced"))
        self.assertEqual(list(model.table), order)
        self.assertEqual(model.table[first][0], b"replaced")
        feed(model, record(b"new", b"value"))
        self.assertNotIn(first, model.table)

    def test_R_and_S_use_visible_equal_capacity_history(self):
        prefix = record(b"Oakford", OAK) + record(b"Pinewell", PINE) + b"{{place|name=Oakford|description="
        models = {arm: codec.Predictor(arm) for arm in "KTRS"}
        for model in models.values():
            feed(model, prefix)
        self.assertEqual(models["T"].donor, OAK)
        self.assertEqual(models["R"].donor, PINE)
        self.assertEqual(models["S"].donor, PINE)
        self.assertEqual(len({model.table_hash for model in models.values()}), 1)
        self.assertEqual(len({codec.canonical(model.table_rows()) for model in models.values()}), 1)

    def test_integer_posterior_and_mismatch_update_order(self):
        model = codec.Predictor()
        feed(model, record(b"x", b"\xff\x00") + b"{{place|name=x|description=")
        self.assertEqual(model.predict(), 49152)
        first = model.state_digest()
        self.assertEqual(model.predict(), 49152)
        self.assertEqual(model.state_digest(), first)
        model.observe(1)
        self.assertEqual(model.predict(), 54613)
        model.observe(0)
        self.assertFalse(model.alive)
        self.assertEqual(model.predict(), 32768)
        model.observe(1)

    def test_predict_must_precede_truth_and_truth_is_bounded(self):
        model = codec.Predictor()
        with self.assertRaises(ValueError):
            model.observe(0)
        model.predict()
        with self.assertRaises(ValueError):
            model.observe(2)
        model.bits = codec.MAX_RAW * 8
        with self.assertRaisesRegex(ValueError, "work bound"):
            model.observe(0)

    def test_checkpoint_restore_in_every_parser_phase(self):
        raw = fixtures()["conditional"] + b"{{bad|name=x|description={{nested}}"
        states = {}
        model = codec.Predictor()
        for index, byte in enumerate(raw):
            feed(model, bytes([byte]))
            states.setdefault(model.parser.mode, (model.serialize(), raw[:index + 1]))
        self.assertTrue({"outside", "name", "key", "value", "close", "invalid"} <= set(states))
        for blob, prefix in states.values():
            a, b = codec.Predictor(), codec.Predictor.restore(blob)
            feed(a, prefix)
            self.assertEqual(a.serialize(), blob)
            self.assertEqual(feed(a, b"|extra=bytes}}"), feed(b, b"|extra=bytes}}"))
            self.assertEqual(a.state_digest(), b.state_digest())

    def test_checkpoint_restore_midbyte_and_mid_donor(self):
        prefix = record(b"Oakford", OAK) + b"{{place|name=Oakford|description="
        for arm in codec.ARMS:
            model = codec.Predictor(arm)
            feed(model, prefix)
            for offset in range(13):
                model.predict()
                other = codec.Predictor.restore(model.serialize())
                self.assertEqual(model.state_digest(), other.state_digest())
                bit = (OAK[offset // 8] >> (7 - offset % 8)) & 1
                self.assertEqual(model.predict(), other.predict())
                model.observe(bit)
                other.observe(bit)
                self.assertEqual(model.serialize(), other.serialize())

    def test_checkpoint_rejects_corruption_bounds_and_false_pending(self):
        model = codec.Predictor("P")
        blob = model.serialize()
        with self.assertRaises(ValueError):
            codec.Predictor.restore(blob[:-1])
        row = model.snapshot()
        row["pending"] = 1
        if self.retained is not None:
            (self.retained / "invalid-uniform-pending.checkpoint").write_bytes(state_blob(row))
        with self.assertRaisesRegex(ValueError, "pending probability"):
            codec.Predictor.restore(state_blob(row))
        row["pending"], row["bits"] = 32768, codec.MAX_RAW * 8
        if self.retained is not None:
            (self.retained / "invalid-pending-at-work-cap.checkpoint").write_bytes(state_blob(row))
        with self.assertRaisesRegex(ValueError, "pending probability"):
            codec.Predictor.restore(state_blob(row))
        row["pending"], row["bits"], row["partial_bits"] = None, 0, 8
        with self.assertRaises(ValueError):
            codec.Predictor.restore(state_blob(row))

    def test_empty_and_boundary_raw(self):
        for arm in codec.ARMS:
            self.exact(b"", arm)
        self.exact(b"\0" * codec.MAX_RAW, "P")
        with self.assertRaisesRegex(ValueError, "raw bound"):
            codec.encode(b"x" * (codec.MAX_RAW + 1))

    def test_archive_rejects_corruption_and_noncanonical_tail(self):
        archive, _ = codec.encode(fixtures()["conditional"])
        for bad in (archive[:10], archive[:-1], archive + b"x", archive[:80] + bytes([archive[80] ^ 1]) + archive[81:]):
            with self.assertRaises(ValueError):
                codec.decode(bad)
        header = list(codec.HEADER.unpack(archive[:codec.HEADER.size]))
        payload = archive[codec.HEADER.size:] + b"\0"
        header[3], header[5] = len(payload), codec.digest(payload)
        with self.assertRaisesRegex(ValueError, "canonical arithmetic"):
            codec.decode(codec.HEADER.pack(*header) + payload)
        header[2] = codec.MAX_RAW + 1
        with self.assertRaisesRegex(ValueError, "raw bound"):
            codec.decode(codec.HEADER.pack(*header) + payload)

    def test_template_key_value_and_field_bounds(self):
        for raw in (b"{{" + b"t" * 33 + b"|a=x|b=y}}", b"{{t|" + b"k" * 33 + b"=x|b=y}}",
                    b"{{t|a=x|b=" + b"v" * 65 + b"}}",
                    b"{{t" + b"".join(b"|k" + str(i).encode() + b"=v" for i in range(9)) + b"}}"):
            model = codec.Predictor()
            feed(model, raw)
            self.assertFalse(model.table)
            self.assertEqual(model.rejected_invocations, 1)
            self.exact(raw, "T")
        raw = b"{{" + b"t" * 32 + b"|" + b"k" * 32 + b"=x|b=" + b"v" * 64 + b"}}"
        model = codec.Predictor()
        feed(model, raw)
        self.assertEqual(len(model.table), 1)

    def test_truncation_at_every_prefix_and_split_brace_pair(self):
        raw = b"{{x|first=a|later=b}}"
        for length in range(len(raw)):
            model = codec.Predictor()
            feed(model, raw[:length])
            self.assertFalse(model.table)
            restored = codec.Predictor.restore(model.serialize())
            feed(model, raw[length:])
            feed(restored, raw[length:])
            self.assertEqual(model.serialize(), restored.serialize())
            self.assertEqual(len(model.table), 1)

    def test_source_inventory_contains_bound_primitives(self):
        inventory = {row["path"]: row for row in codec.source_inventory()}
        for name, expected in codec.SOURCE_PINS.items():
            self.assertEqual(inventory["tools/" + name]["sha256"], expected)
        self.assertIn("tools/causal_field_dependency_v1.py", inventory)

    def test_independent_cli_roundtrips_and_repeats(self):
        with tempfile.TemporaryDirectory(prefix="gamma-causal-field-cli-") as temporary:
            directory = Path(temporary)
            source = directory / "synthetic.raw"
            source.write_bytes(fixtures()["conditional"])
            executions = []
            for arm in codec.ARMS:
                reports = []
                for operation, origin, target in (("encode", source, directory / (arm + ".archive")),
                        ("decode", directory / (arm + ".archive"), directory / (arm + ".raw")),
                        ("repeat", directory / (arm + ".raw"), directory / (arm + ".repeat"))):
                    command = [sys.executable, str(Path(codec.__file__)), operation, str(origin), str(target), "--arm", arm]
                    completed = subprocess.run(command, capture_output=True, text=True, timeout=20, check=True,
                        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
                    reports.append(json.loads(completed.stdout)["result"])
                    (directory / (arm + "." + operation + ".json")).write_text(completed.stdout)
                    (directory / (arm + "." + operation + ".stderr")).write_text(completed.stderr)
                    executions.append({"arm": arm, "operation": operation, "command": command,
                                       "returncode": completed.returncode, "source_bytes": origin.stat().st_size,
                                       "source_sha256": hashlib.sha256(origin.read_bytes()).hexdigest(),
                                       "output_bytes": target.stat().st_size, "output_sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
                self.assertEqual((directory / (arm + ".raw")).read_bytes(), source.read_bytes())
                self.assertEqual((directory / (arm + ".archive")).read_bytes(), (directory / (arm + ".repeat")).read_bytes())
                self.assertEqual(reports[0], reports[1])
                self.assertEqual(reports[0], reports[2])
            repeated = subprocess.run([sys.executable, str(Path(codec.__file__)), "encode", str(source),
                str(directory / "P.archive"), "--arm", "P"], capture_output=True, timeout=20)
            self.assertNotEqual(repeated.returncode, 0)
            if self.retained is not None:
                inventory = codec.source_inventory()
                (directory / "execution-receipt.json").write_text(json.dumps({"synthetic_only": True, "native_processes": len(executions),
                    "executions": executions, "source_files": inventory, "local_source_bytes": sum(row["bytes"] for row in inventory),
                    "complete_package_bytes": None, "objective_credit_bytes": 0, "qualification_authority": False,
                    "resources": {"cpus": sorted(os.sched_getaffinity(0)), "address_space_limit": resource.getrlimit(resource.RLIMIT_AS),
                                  "cpu_limit": resource.getrlimit(resource.RLIMIT_CPU)}}, sort_keys=True, indent=2) + "\n")
                shutil.copytree(directory, self.retained / "independent-cli")


if __name__ == "__main__":
    unittest.main()
