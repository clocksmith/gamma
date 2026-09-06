"""Synthetic driver boundaries only; no subprocess or published corpus reads."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


runner = load("schema_transfer_test_runner", ROOT / "tools/wiki_schema_exact_transfer250k_q0_v1.py")
codec = load("schema_transfer_test_codec", ROOT / "tools/wiki_schema_exact_codec_v1.py")


class FakeGate:
    def __init__(self, root, alter=None):
        self.root, self.result = root, root / "results" / runner.ID
        self.work = self.result / "work"
        (self.work / "tmp").mkdir(parents=True)
        self.buffers = {runner.CODEC: (ROOT / runner.CODEC).read_bytes()}
        self.codec_path = self.work / "codec.py"
        self.codec_path.write_bytes(self.buffers[runner.CODEC])
        self.commands, self.required, self.alter, self.closed = [], set(), alter, True

    def run(self, name, argv, cap):
        self.commands.append({"phase": name, "returncode": 0})
        assert cap == 120 and "--as=536870912" in argv and "--cpu=120" in argv
        assert "--fsize=33554432" in argv and "-I" in argv and "-S" in argv and "-B" in argv
        arguments = argv[argv.index(str(self.codec_path))+1:]
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
            code = codec.main(arguments)
        assert code == 0, err.getvalue()
        receipt_path = Path(arguments[arguments.index("--receipt")+1])
        if self.alter:
            self.alter(name, receipt_path, Path(arguments[2]))
            stdout = receipt_path.read_text()
        else:
            stdout = out.getvalue()
        (self.result / (name + ".stdout")).write_text(stdout)
        (self.result / (name + ".stderr")).write_text(err.getvalue())

    def artifact(self, path):
        data = path.read_bytes()
        return {"path": str(path.relative_to(self.root)), "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest()}

    def write(self, name, value):
        (self.result / name).write_text(json.dumps(value))

    def closure(self):
        if not self.closed:
            raise ValueError("owned child remains")

    def verify(self):
        pass


class SchemaTransferTests(unittest.TestCase):
    def population(self, gate, name="tiny"):
        raw = b"<x>A</x>\n"*7 + b"\x00\xff"
        (gate.work / (name + ".raw")).write_bytes(raw)
        return {"name": name, "offset": 0, "bytes": len(raw), "sha256": runner.digest(raw)}

    def test_twenty_four_fake_phases_and_no_false_control_activation(self):
        with tempfile.TemporaryDirectory() as directory:
            gate = FakeGate(Path(directory))
            for name in ("first", "second"):
                measured = runner.compare_population(gate, gate.codec_path,
                    {"python_executable": sys.executable}, self.population(gate, name))
                self.assertTrue(measured["D_framed_P_bound_pass"])
                self.assertTrue(measured["all_arm_dictionary_states_equal"])
                self.assertFalse(measured["selected_C_control_active"])
                self.assertEqual(measured["control_outcome"], "inactive")
                for arm in runner.ARMS:
                    self.assertTrue(measured["arms"][arm]["roundtrip_ok"])
                    self.assertTrue(measured["arms"][arm]["deterministic_ok"])
            self.assertEqual(len(gate.commands), 24)

    def test_unselected_grammar_queries_do_not_activate_control(self):
        def alter(name, receipt_path, output):
            if "-C-" in name and not name.endswith("decode"):
                receipt = json.loads(receipt_path.read_text())
                for row in receipt["blocks"]:
                    self.assertEqual(row["mode"], 0)
                    row["grammar_proposal"].update(shuffled_queries=123, shuffled_associations=123, references=123)
                receipt_path.write_text(json.dumps(receipt))
        with tempfile.TemporaryDirectory() as directory:
            gate = FakeGate(Path(directory), alter)
            result = runner.compare_population(gate, gate.codec_path, {"python_executable": sys.executable}, self.population(gate))
            self.assertFalse(result["selected_C_control_active"])
            self.assertEqual(result["arms"]["C"]["selected_grammar_counts"]["shuffled_associations"], 0)

    def test_dictionary_divergence_is_rejected(self):
        def alter(name, receipt_path, output):
            if name.endswith("-D-decode"):
                receipt = json.loads(receipt_path.read_text())
                receipt["blocks"][0]["dictionary_after"] = "0"*64
                receipt_path.write_text(json.dumps(receipt))
        with tempfile.TemporaryDirectory() as directory:
            gate = FakeGate(Path(directory), alter)
            with self.assertRaisesRegex(ValueError, "dictionary digests differ"):
                runner.compare_population(gate, gate.codec_path, {"python_executable": sys.executable}, self.population(gate))

    def test_accounting_rejects_omitted_envelope_byte(self):
        archive, receipt = codec.encode(b"tiny", arm="D", **runner.OPTIONS)
        receipt["accounting"]["H_bits"] -= 8
        with self.assertRaisesRegex(ValueError, "framing accounting differs"):
            runner.validate_accounting(receipt, len(archive), 4)

    def test_ambiguous_kill_is_not_budget_evidence(self):
        self.assertEqual(runner.classify(types.SimpleNamespace(category="resource_or_signal_stop"), [{"returncode": 137}]),
                         "resource_or_signal_stop")
        self.assertEqual(runner.classify(types.SimpleNamespace(category="budget_exhausted"), [{"returncode": 124}]),
                         "budget_exhausted")
        self.assertEqual(runner.classify(ValueError("malformed receipt")), "implementation_or_infrastructure_failure")

    def test_failed_receipt_retains_published_output_in_artifact_index(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            gate = FakeGate(root)
            output, missing = gate.result / "encode.bin", gate.result / "encode.receipt.json"
            output.write_bytes(b"already published")
            gate.required.update((output, missing))
            stage = {"status": "failed", "infrastructure_pass": False, "promotion_authorized": False}
            with mock.patch.object(runner, "ROOT", root), mock.patch.object(runner, "verify_runtime", return_value={}):
                runner.finalize(gate, stage, {})
            index = json.loads((gate.result / "artifacts.json").read_text())
            self.assertIn(str(output.relative_to(root)), {row["path"] for row in index["files"]})
            self.assertFalse(index["complete"])
            self.assertFalse(stage["infrastructure_pass"])
            self.assertTrue(any(row["path"] == str(missing) for row in index["errors"]))

    def test_unclosed_child_prevents_artifact_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            gate = FakeGate(root)
            gate.closed = False
            stage = {"status": "passed", "infrastructure_pass": True, "promotion_authorized": False}
            with mock.patch.object(runner, "ROOT", root), mock.patch.object(runner, "read_bytes", side_effect=AssertionError("live artifact read")):
                runner.finalize(gate, stage, {})
            self.assertFalse(stage["child_closure_ok"])
            self.assertFalse(stage["infrastructure_pass"])
            self.assertEqual(json.loads((gate.result / "artifacts.json").read_text())["files"], [])


if __name__ == "__main__":
    unittest.main()
