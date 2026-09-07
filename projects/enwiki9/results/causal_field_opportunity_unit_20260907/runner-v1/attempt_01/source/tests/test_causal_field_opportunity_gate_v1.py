"""The observation runner must fail before interpreting mismatched state or input."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import causal_field_opportunity_gate_v1 as gate
import causal_field_opportunity_v1 as observer


def fixture():
    raw = b"{{place|name=A|text=alpha}}{{place|name=B|text=beta}}{{place|name=A|text=alpha}}"
    # This fixture uses only bytes outside WRT's reserved literal values.
    modeled = b"\7" + bytes(observer.base.wrt.wrt_byte_transform(b) for b in raw)
    return raw, modeled


class ScanTests(unittest.TestCase):
    def test_scan_binds_complete_reconstructed_identity_and_original_state(self):
        raw, modeled = fixture()
        expected = observer.base.Adapter([], "T", len(raw))
        for byte in modeled:
            expected.feed(byte)
        expected.finish()
        report = gate.scan(observer, modeled, [], len(raw), hashlib.sha256(raw).hexdigest(), expected.stats())
        self.assertTrue(report["retained_terminal_state_agreement"])
        self.assertEqual(report["diagnostics"]["inherited_selected_starts"], 1)
        self.assertEqual(report["diagnostics"]["conditional"]["exact_compatible_hit"], 1)
        again = gate.scan(observer, modeled, [], len(raw), hashlib.sha256(raw).hexdigest(), expected.stats())
        self.assertEqual(report, again)
        self.assertIsNone(report["archive_bytes"])
        self.assertEqual(report["objective_credit_bytes"], 0)

    def test_wrong_raw_hash_and_terminal_expectation_fail(self):
        raw, modeled = fixture()
        with self.assertRaisesRegex(ValueError, "raw identity mismatch"):
            gate.scan(observer, modeled, [], len(raw), "0" * 64)
        with self.assertRaisesRegex(ValueError, "retained corpus adapter"):
            gate.scan(observer, modeled, [], len(raw), hashlib.sha256(raw).hexdigest(), {})

    def test_first_intermediate_state_divergence_fails_even_if_terminal_would_agree(self):
        class Broken(observer.Adapter):
            def state_digest(self):
                return "0" * 64 if self.modeled_count == 9 else super().state_digest()
        raw, modeled = fixture()
        with self.assertRaisesRegex(ValueError, "state divergence at modeled byte 8"):
            gate.scan(SimpleNamespace(base=observer.base, Adapter=Broken), modeled, [], len(raw), hashlib.sha256(raw).hexdigest())

    def test_first_emission_divergence_fails(self):
        class Broken(observer.Adapter):
            def feed(self, byte):
                output = super().feed(byte)
                return output + b"!" if self.modeled_count == 9 else output
        raw, modeled = fixture()
        with self.assertRaisesRegex(ValueError, "raw emission divergence at modeled byte 8"):
            gate.scan(SimpleNamespace(base=observer.base, Adapter=Broken), modeled, [], len(raw), hashlib.sha256(raw).hexdigest())

    def test_malformed_or_overbound_population_fails(self):
        with self.assertRaises(ValueError):
            gate.scan(observer, b"\7\0", [], 250001, "0" * 64)
        with self.assertRaisesRegex(ValueError, "modeled bound"):
            gate.scan(observer, b"\7" * 4097, [], 0, "0" * 64)
        with self.assertRaises(ValueError):
            gate.scan(observer, b"", [], 0, hashlib.sha256(b"").hexdigest())


class BindingTests(unittest.TestCase):
    def test_digest_bounds_and_aliases(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").write_bytes(b"abc")
            reference = {"path": "data", "sha256": "sha256:" + hashlib.sha256(b"abc").hexdigest()}
            self.assertEqual(gate.bound_read(root, reference, 3), b"abc")
            with self.assertRaisesRegex(ValueError, "read bound"):
                gate.bound_read(root, reference, 2)
            with self.assertRaisesRegex(ValueError, "digest changed"):
                gate.bound_read(root, {**reference, "sha256": "0" * 64})
            (root / "alias").symlink_to(root / "data")
            with self.assertRaisesRegex(ValueError, "aliased input"):
                gate.bound_read(root, {**reference, "path": "alias"})
            with self.assertRaisesRegex(ValueError, "aliased input"):
                gate.bound_read(root, {**reference, "path": "../data"})

    def test_same_content_replacement_during_read_fails_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "data"
            target.write_bytes(b"abc")
            reference = {"path": "data", "sha256": hashlib.sha256(b"abc").hexdigest()}
            stat = Path.stat
            def changed(path, *args, **kwargs):
                if path == target:
                    replacement = root / "replacement"
                    replacement.write_bytes(b"abc")
                    replacement.replace(target)
                return stat(path, *args, **kwargs)
            # The final pathname identity is checked even when bytes still hash equally.
            with patch.object(Path, "stat", changed), self.assertRaisesRegex(ValueError, "input replaced"):
                gate.bound_read(root, reference)


if __name__ == "__main__":
    unittest.main()
