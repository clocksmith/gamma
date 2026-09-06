"""Independent exact-residual goldens and bounded synthetic probe checks.

No compiler, model, corpus or installation is invoked here. A canonical caller
provides an already-built executable in FX2_EXACT_RESIDUAL_PROBE and owns CPU,
memory and aggregate limits. The fixed parent fixture writer is stdlib-only.
This reference shares its public range arithmetic and metadata serialization,
but independently specifies the signed-byte approximation/residual pairing.
Preserve the upstream GPLv3 provenance of fx2_weight_marginal_fixtures_v1.py.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest import mock

PROJECT = Path(__file__).resolve().parents[1]
REFERENCE = PROJECT / "tools/fx2_weight_marginal_fixtures_v1.py"
spec = importlib.util.spec_from_file_location("fx2_exact_parent_reference", REFERENCE)
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)
MAGIC = b"GFX2XOR1"
APPROXIMATION = (-6, -6, -4, -4, -4, -2, 0, 0, 0, 2, 4, 4, 4, 6, 6)
RESIDUALS = (0, 1, 3, 7, 255)
ERROR_PREFIX = b"fx2_weight_exact_residual_probe_v1: "


def assert_expected_rejection(test, result):
    """A codec validation error is distinct from a crash or unrelated failure."""
    test.assertEqual(result.returncode, 1, (result.returncode, result.stdout, result.stderr))
    test.assertTrue(result.stderr.startswith(ERROR_PREFIX), result.stderr)


def pair(q):
    if type(q) is not int or not -7 <= q <= 7:
        raise ValueError("not an original signed INT4 value")
    hat = APPROXIMATION[q + 7]
    residual = (q & 255) ^ (hat & 255)
    restored = (hat & 255) ^ residual
    assert (restored if restored < 128 else restored - 256) == q
    return (hat + 6) // 2, RESIDUALS.index(residual)


def factor_counts(original):
    approximation = [0] * 8
    residual = [[0] * 8 for _ in range(7)]
    for symbol, count in enumerate(original):
        a, e = pair(symbol - 7)
        approximation[a] += count
        residual[a][e] += count
    return approximation, residual


def put_fixed(writer, counts, symbol):
    """Use interval slices, independently of the native heap-array tree."""
    assert len(counts) == 8 and counts[symbol] > 0
    start, width = 0, 8
    while width > 1:
        half = width // 2
        left, right = sum(counts[start:start + half]), sum(counts[start + half:start + width])
        bit = int(symbol >= start + half)
        if left and right:
            total = left + right
            probability = max(1, min(2047, (2048 * left + total // 2) // total))
            writer.bit(probability, bit)
        else:
            assert bit == int(left == 0)
        start += half * bit
        width = half


def encode_exact_reference(tensors, *, supplied_histograms=None):
    local = reference.histograms(tensors) if supplied_histograms is None else supplied_histograms
    header, _ = reference.header(len(tensors), "D", local)
    writer, previous_meta = reference.RangeWriter(), 0

    def meta(value):
        nonlocal previous_meta
        writer.symbol("metadata", previous_meta, 8, value)
        previous_meta = value

    for index, tensor in enumerate(tensors):
        name = tensor["name"].encode()
        meta(len(name))
        context = (0, 0)
        for value in name:
            writer.symbol("name", context, 8, value)
            context = (context[1], value)
        meta(tensor["dtype"])
        meta(len(tensor["shape"]))
        for extent in tensor["shape"]:
            for value in struct.pack("<I", extent):
                meta(value)
        encoding, payload = tensor["encoding"], tensor["payload"]
        meta(encoding)
        if encoding == reference.INT4:
            approximate, conditional = factor_counts(local[index])
            for q in payload:
                a, e = pair(q)
                put_fixed(writer, approximate, a)
                put_fixed(writer, conditional[a], e)
        elif encoding == reference.BF16:
            for offset in range(0, len(payload), 2):
                low, high = payload[offset:offset + 2]
                writer.symbol("bf16_hi", 0, 8, high)
                writer.symbol("bf16_lo", high, 8, low)
        elif encoding == reference.PLANE4:
            for offset, value in enumerate(payload):
                writer.symbol("plane", offset % 4, 8, value)
        elif encoding == reference.RAW:
            for value in payload:
                writer.symbol("raw", 0, 8, value)
        else:
            assert encoding in (reference.ROPE_SIN, reference.ROPE_COS)
    return MAGIC + header[8:] + writer.finish()


def exact_rejection_streams():
    tensors = reference.valid_populations()["heterogeneous_tensors"]
    valid = encode_exact_reference(tensors)
    stream = 77 + 64 * len(reference.histograms(tensors))
    u32 = reference.replace_u32
    cases = {
        "mode": valid[:12] + b"\2" + valid[13:],
        "tensor_limit": u32(valid, 8, 4097),
        "record_count": u32(valid, 13, 4097),
        "global_sum": u32(valid, 17, 0),
        "index": u32(valid, 77, len(tensors)),
        "duplicate": u32(valid, 141, 0),
        "unsorted": valid[:77] + valid[141:205] + valid[77:141] + valid[205:],
        "missing_empty_record": u32(valid[:205] + valid[269:], 13, 2),
        "cache": valid[:stream] + b"\1" + valid[stream + 1:],
        "short_header": valid[:76],
        "short_record": valid[:140],
        "short_stream": valid[:stream + 4],
        "flush": valid[:-1],
        "trailing": valid + b"\0",
    }
    # Encode the actual values using intentionally false paid probabilities;
    # this must fail decoded histogram validation, rather than relying on luck.
    wrong = reference.histograms(tensors)
    wrong[0][0] -= 1
    wrong[0][1] += 1
    cases["decoded_histogram"] = encode_exact_reference(tensors, supplied_histograms=wrong)
    wrong = reference.histograms(tensors)
    wrong[0][0] += 1
    cases["shape_sum"] = encode_exact_reference(tensors, supplied_histograms=wrong)
    return cases


class ReferenceTests(unittest.TestCase):
    def test_signed_bit_mapping_is_bijective(self):
        pairs = {pair(q) for q in range(-7, 8)}
        self.assertEqual(len(pairs), 15)
        self.assertEqual({RESIDUALS[e] for _, e in pairs}, set(RESIDUALS))
        self.assertEqual(pair(-1), (3, 4))  # -1 XOR +0 is 0xff, not a small signed error.

    def test_crash_abort_and_unrelated_errors_cannot_pass_rejection(self):
        for code in (-11, -6, 139, 134, 2, 0):
            result = mock.Mock(returncode=code, stdout=b"", stderr=ERROR_PREFIX + b"mock diagnostic\n")
            with self.subTest(returncode=code), self.assertRaises(AssertionError):
                assert_expected_rejection(self, result)
        result = mock.Mock(returncode=1, stdout=b"", stderr=b"an unrelated launcher error\n")
        with self.assertRaises(AssertionError):
            assert_expected_rejection(self, result)
        assert_expected_rejection(self, mock.Mock(returncode=1, stdout=b"", stderr=ERROR_PREFIX + b"invalid input\n"))


@unittest.skipUnless(os.environ.get("FX2_EXACT_RESIDUAL_PROBE"), "requires an explicitly supplied bounded probe")
class NativeSyntheticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.probe = str(Path(os.environ["FX2_EXACT_RESIDUAL_PROBE"]).resolve(strict=True))

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="fx2-exact-residual-")
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.sequence = 0

    def invoke(self, mode, data, *, accepted=True):
        self.sequence += 1
        source = self.work / f"input-{self.sequence}"
        output = self.work / f"output-{self.sequence}"
        source.write_bytes(data)
        result = subprocess.run([self.probe, mode, str(source), str(output)], capture_output=True, timeout=15)
        if not accepted:
            assert_expected_rejection(self, result)
            self.assertFalse(output.exists())
            self.assertFalse(Path(str(output) + ".partial").exists())
            return None, result
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        receipt = json.loads(result.stdout)
        self.assertTrue(receipt["original_stream_regeneration_ok"])
        self.assertTrue(receipt["original_parameter_bits_exact"])
        self.assertTrue(receipt["inverse_ok"])
        self.assertTrue(receipt["repeat_ok"])
        self.assertIsNone(receipt["complete_package_bytes"])
        self.assertFalse(receipt["inference_executed"])
        return output.read_bytes(), receipt

    def test_self_test(self):
        result = subprocess.run([self.probe, "--self-test"], capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["all_15_signed_values_exact"])

    def test_all_parent_populations_exact_goldens_and_fresh_repeats(self):
        for name, tensors in reference.valid_populations().items():
            with self.subTest(population=name):
                original = reference.encode_reference(tensors)
                selected = reference.encode_reference(tensors, "D")
                golden = encode_exact_reference(tensors)
                p, p_receipt = self.invoke("P", original)
                k, _ = self.invoke("K", selected)
                d, d_receipt = self.invoke("D", selected)
                restored, _ = self.invoke("restore", d)
                repeated, _ = self.invoke("D", original)
                self.assertEqual(p, selected)
                self.assertEqual(k, selected)
                self.assertEqual(d, golden)
                self.assertEqual(repeated, d)
                self.assertEqual(restored, original)
                self.assertEqual(hashlib.sha256(restored).hexdigest(), hashlib.sha256(original).hexdigest())
                self.assertEqual(p_receipt["tensors"], d_receipt["tensors"])
                self.assertEqual(d_receipt["header_bytes"], 77 + 64 * len(reference.histograms(tensors)))

    def test_every_prior_malformed_parent_and_marginal_is_rejected(self):
        for name, (mode, data) in reference.rejection_streams(reference.valid_populations()).items():
            with self.subTest(case=name):
                self.invoke(mode, data, accepted=False)

    def test_exact_container_rejects_malformed_counts_bounds_and_closure(self):
        for name, data in exact_rejection_streams().items():
            with self.subTest(case=name):
                self.invoke("restore", data, accepted=False)

    def test_publication_is_exclusive_and_stdout_failure_is_visible(self):
        source = self.work / "source"
        source.write_bytes(reference.encode_reference(reference.valid_populations()["empty_and_scalar"]))
        output = self.work / "output"
        sentinel = b"preserve existing output\n"
        output.write_bytes(sentinel)
        result = subprocess.run([self.probe, "P", str(source), str(output)], capture_output=True, timeout=15)
        assert_expected_rejection(self, result)
        self.assertEqual(output.read_bytes(), sentinel)
        self.assertFalse(Path(str(output) + ".partial").exists())
        output.unlink()
        partial = Path(str(output) + ".partial")
        partial.write_bytes(sentinel)
        result = subprocess.run([self.probe, "P", str(source), str(output)], capture_output=True, timeout=15)
        assert_expected_rejection(self, result)
        self.assertEqual(partial.read_bytes(), sentinel)
        self.assertFalse(output.exists())
        partial.unlink()
        if Path("/dev/full").exists():
            with Path("/dev/full").open("wb") as sink:
                result = subprocess.run([self.probe, "P", str(source), str(output)], stdout=sink, stderr=subprocess.PIPE, timeout=15)
            assert_expected_rejection(self, result)
            self.assertIn(b"receipt stdout flush failed", result.stderr)
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
