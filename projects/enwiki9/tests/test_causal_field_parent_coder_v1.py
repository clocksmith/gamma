#!/usr/bin/env python3
"""Synthetic arithmetic references; optional retained outputs use an explicit path."""

import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from causal_field_parent_coder_v1 import (  # noqa: E402
    Decoder, Encoder, ParentMixture, MAX_BITS, MAX_DONOR_BYTES, NATIVE_REFERENCE_SOURCES,
)


def bits(raw):
    return [(byte >> shift) & 1 for byte in raw for shift in range(7, -1, -1)]


def reference_encode(truth, probabilities):
    """The native two-part split, independent of the production full product."""
    left, right, output, states = 0, 0xFFFFFFFF, bytearray(), []
    for bit, q in zip(truth, probabilities, strict=True):
        width = right - left
        split = left + (width >> 16) * q + (((width & 65535) * q) >> 16)
        left, right = (left, split) if bit else (split + 1, right)
        while left >> 24 == right >> 24:
            output.append(right >> 24)
            left = (left * 256) % 2**32
            right = (right * 256 + 255) % 2**32
        states.append((left, right))
    output.append(right >> 24)
    return bytes(output), states


class RangeCoderTests(unittest.TestCase):
    def exercise(self, truth, probabilities):
        expected, states = reference_encode(truth, probabilities)
        encoder = Encoder(max_bits=len(truth))
        for bit, q, state in zip(truth, probabilities, states, strict=True):
            encoder.encode(bit, q)
            self.assertEqual((encoder.low, encoder.high), state)
        payload = encoder.finish()
        self.assertEqual(payload, expected)
        self.assertEqual(encoder.finish(), payload)
        decoder = Decoder(payload, max_bits=len(truth), expected_payload_bytes=len(payload),
                          payload_sha256=hashlib.sha256(payload).hexdigest())
        repeat = Encoder(max_bits=len(truth))
        for bit, q, state in zip(truth, probabilities, states, strict=True):
            found = decoder.decode(q)
            self.assertEqual(found, bit)
            self.assertEqual((decoder.low, decoder.high), state)
            repeat.encode(found, q)
        self.assertEqual(repeat.finish(), payload)
        return payload

    def test_empty_native_flush_and_single_bit_extremes(self):
        self.assertEqual(self.exercise([], []), b"\xff")
        for q in (1, 2, 32767, 32768, 65534, 65535):
            for bit in (0, 1):
                self.exercise([bit], [q])

    def test_extreme_and_varying_probabilities_exact(self):
        rng = random.Random(119)
        truth = bits(bytes(rng.randrange(256) for _ in range(256)))
        for probabilities in ([1] * len(truth), [65535] * len(truth),
                              [rng.randrange(1, 65536) for _ in truth]):
            self.exercise(truth, probabilities)

    def test_native_zero_fill_requires_external_framing(self):
        truth = bits(bytes(range(32)))
        payload = self.exercise(truth, [32768] * len(truth))
        self.assertGreater(len(payload), 1)
        # The native constructor accepts a truncated nonempty raw payload.
        Decoder(payload[:-1], max_bits=len(truth))
        with self.assertRaisesRegex(ValueError, "length"):
            Decoder(payload[:-1], expected_payload_bytes=len(payload))
        with self.assertRaisesRegex(ValueError, "digest"):
            Decoder(payload[:-1] + bytes([payload[-1] ^ 1]),
                    payload_sha256=hashlib.sha256(payload).hexdigest())
        decoder = Decoder(payload + b"\x00", max_bits=len(truth))
        decoded = [decoder.decode(32768) for _ in truth]
        self.assertEqual(decoded, truth)
        self.assertNotEqual(reference_encode(decoded, [32768] * len(truth))[0], payload + b"\x00")

    def test_invalid_arguments_do_not_advance_state(self):
        encoder = Encoder()
        decoder = Decoder(b"\xff")
        for q in (0, 65536, True, 0.5, "1", None):
            with self.assertRaises(ValueError):
                encoder.encode(1, q)
            with self.assertRaises(ValueError):
                decoder.decode(q)
        for bit in (-1, 2, True, 0.0, None):
            with self.assertRaises(ValueError):
                encoder.encode(bit, 32768)
        self.assertEqual((encoder.low, encoder.high, encoder.bit_count), (0, 0xFFFFFFFF, 0))
        self.assertEqual((decoder.low, decoder.high, decoder.bit_count), (0, 0xFFFFFFFF, 0))
        for payload in (b"", bytearray(b"x"), "x", None):
            with self.assertRaises(ValueError):
                Decoder(payload)
        for h in (True, "A" * 64, "f" * 63):
            with self.assertRaises(ValueError):
                Decoder(b"x", payload_sha256=h)

    def test_work_payload_and_closed_encoder_bounds(self):
        for n in (-1, True, MAX_BITS + 1):
            with self.assertRaises(ValueError):
                Encoder(max_bits=n)
        encoder = Encoder(max_bits=0)
        with self.assertRaises(ValueError):
            encoder.encode(0, 1)
        self.assertEqual(encoder.finish(), b"\xff")
        decoder = Decoder(b"\xff", max_bits=0)
        with self.assertRaises(ValueError):
            decoder.decode(1)
        encoder = Encoder(max_payload_bytes=1)
        with self.assertRaisesRegex(ValueError, "payload"):
            encoder.encode(1, 1)
        self.assertEqual((encoder.low, encoder.high, encoder.bit_count), (0, 0xFFFFFFFF, 0))
        encoder.finish()
        with self.assertRaisesRegex(ValueError, "finished"):
            encoder.encode(0, 32768)
        with self.assertRaises(ValueError):
            Decoder(b"12", max_payload_bytes=1)

    def test_pinned_native_cpp_interval_and_payload_oracle(self):
        """Compile the pinned native methods, substituting only their Q16 input.

        Float discretization and trace instrumentation are intentionally removed:
        this API consumes the integer q that follows native discretization.
        """
        methods = []
        for name, expected in NATIVE_REFERENCE_SOURCES.items():
            raw = (ROOT / name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected)
            lines = []
            for line in raw.decode().splitlines():
                if line.startswith("#include") or "gamma_record" in line:
                    continue
                if "const float gamma_probability" in line:
                    lines.append("  const unsigned int p = p_->Predict();")
                elif "const unsigned int p = Discretize" not in line:
                    lines.append(line)
            methods.append("\n".join(lines))
        prefix = r'''
#include <fstream>
#include <iostream>
#include <vector>
struct Predictor {
  std::vector<unsigned> q; unsigned pos=0;
  unsigned Predict() { return q.at(pos); }
  void Perceive(int) { ++pos; }
};
struct Encoder {
  std::ofstream* os_; unsigned x1_,x2_; Predictor* p_; std::vector<unsigned char> out_;
  Encoder(std::ofstream*,Predictor*); void WriteByte(unsigned); unsigned Discretize(float);
  void Encode(int); void Flush();
};
struct Decoder {
  std::ifstream* is_; unsigned x1_,x2_,x_; Predictor* p_;
  Decoder(std::ifstream*,Predictor*); int ReadByte(); unsigned Discretize(float); int Decode();
};
'''
        suffix = r'''
int main(int argc,char** argv) {
  if(argc!=2) return 2;
  unsigned n; if(!(std::cin>>n)||n>65536) return 3;
  Predictor pe,pd; std::vector<unsigned> bits;
  for(unsigned i=0;i<n;++i) {unsigned q,b; if(!(std::cin>>q>>b)||!q||q>65535||b>1) return 4;
    pe.q.push_back(q); pd.q.push_back(q); bits.push_back(b);}
  std::ofstream out(argv[1],std::ios::binary); Encoder e(&out,&pe);
  for(unsigned b:bits) {e.Encode(b); std::cout<<"E "<<e.x1_<<" "<<e.x2_<<"\n";}
  e.Flush(); out.close(); std::ifstream in(argv[1],std::ios::binary); Decoder d(&in,&pd);
  for(unsigned i=0;i<n;++i) {int b=d.Decode(); std::cout<<"D "<<b<<" "<<d.x1_<<" "<<d.x2_<<"\n";}
}
'''
        retained = os.environ.get("GAMMA_PARENT_CODER_TEST_ARTIFACTS")
        with tempfile.TemporaryDirectory(prefix="field-parent-native-") as temporary:
            directory = Path(temporary)
            if retained:
                directory = Path(retained) / "native-oracle"
                directory.mkdir(parents=True, exist_ok=False)
            source, executable, payload = directory / "oracle.cpp", directory / "oracle", directory / "payload.bin"
            source.write_text(prefix + "\n".join(methods) + suffix)
            built = subprocess.run(["g++", "-std=c++17", "-O2", "-fno-fast-math", str(source), "-o", str(executable)],
                                   capture_output=True, timeout=30)
            (directory / "build.stdout").write_bytes(built.stdout)
            (directory / "build.stderr").write_bytes(built.stderr)
            self.assertEqual(built.returncode, 0, built.stderr.decode())
            rng = random.Random(1297)
            truth = bits(bytes(rng.randrange(256) for _ in range(64)))
            probabilities = [rng.choice([1, 2, 32768, 65534, 65535, rng.randrange(1, 65536)]) for _ in truth]
            stdin = str(len(truth)) + "\n" + "".join(f"{q} {b}\n" for q, b in zip(probabilities, truth))
            (directory / "input.txt").write_text(stdin)
            run = subprocess.run([str(executable), str(payload)], input=stdin.encode(), capture_output=True, timeout=10)
            (directory / "run.stdout").write_bytes(run.stdout)
            (directory / "run.stderr").write_bytes(run.stderr)
            self.assertEqual(run.returncode, 0, run.stderr.decode())
            expected, states = reference_encode(truth, probabilities)
            lines = run.stdout.decode().splitlines()
            self.assertEqual(lines[:len(truth)], [f"E {low} {high}" for low, high in states])
            self.assertEqual(lines[len(truth):], [f"D {b} {low} {high}" for b, (low, high) in zip(truth, states)])
            self.assertEqual(payload.read_bytes(), self.exercise(truth, probabilities))
            self.assertEqual(payload.read_bytes(), expected)


class ParentMixtureTests(unittest.TestCase):
    def compare_reference(self, donor, truth, probabilities):
        model = ParentMixture(max_bits=len(truth))
        model.reset(donor)
        donor_bits = bits(donor) if donor is not None else []
        parent_weight = Fraction(1, 2)
        donor_weight = Fraction(1, 2) if donor_bits else Fraction(0)
        for i, (bit, q) in enumerate(zip(truth, probabilities, strict=True)):
            p = Fraction(q, 65536)
            active = i < len(donor_bits) and donor_weight != 0
            mixed = (parent_weight * p + donor_weight * donor_bits[i]) / (parent_weight + donor_weight) if active else p
            expected = max(1, min(65535, (mixed * 65536).numerator // (mixed * 65536).denominator))
            self.assertEqual(model.predict(q), expected)
            self.assertEqual(model.export()["pending"]["parent_q"], q)
            model.observe(bit)
            if active:
                parent_weight *= p if bit else 1 - p
                donor_weight *= int(bit == donor_bits[i])
            state = model.export()
            if donor_weight:
                self.assertEqual(Fraction(int(state["donor_mass_hex"], 16), int(state["parent_mass_hex"], 16)),
                                 donor_weight / parent_weight)
            else:
                self.assertEqual(int(state["donor_mass_hex"], 16), 0)
        return model

    def test_fraction_reference_extremes_nonuniform_and_mismatches(self):
        rng = random.Random(317)
        for donor in (b"\x00" * 8, b"\xff" * 8, bytes(range(8))):
            original = bits(donor)
            for mismatch in (None, 0, 7, 31, 63):
                truth = original.copy()
                if mismatch is not None:
                    truth[mismatch] ^= 1
                for qs in ([1] * 64, [65535] * 64, [rng.randrange(1, 65536) for _ in truth]):
                    self.compare_reference(donor, truth, qs)

    def test_none_empty_and_exhaustion_return_parent(self):
        for donor in (None, b"", b"\xaa"):
            truth = bits(b"\xaa\x80\xff")
            self.compare_reference(donor, truth, [12345, 65535, 1] * 8)

    def test_parent_truth_probability_not_mixed_probability_updates_mass(self):
        model = ParentMixture()
        model.reset(b"\xff")
        self.assertEqual(model.predict(10000), 37768)
        model.observe(1)
        self.assertEqual(model.predict(50000), (10000 * 50000 + 65536 * 65536) // (10000 + 65536))
        model.observe(1)
        self.assertEqual(Fraction(int(model.export()["donor_mass_hex"], 16), int(model.export()["parent_mass_hex"], 16)),
                         Fraction(65536**2, 10000 * 50000))

    def test_mismatch_and_exhaustion_stop_integer_growth(self):
        for mismatch in (False, True):
            model = ParentMixture(max_bits=2048)
            model.reset(b"\xff")
            for i in range(8):
                model.predict(1)
                model.observe(0 if mismatch and i == 0 else 1)
            old = model.export()
            for _ in range(2040):
                self.assertEqual(model.predict(123), 123)
                model.observe(1)
            new = model.export()
            for key in ("donor_mass_hex", "parent_mass_hex", "donor_bit_position"):
                self.assertEqual(old[key], new[key])

    def test_maximum_donor_export_and_digest_are_bounded(self):
        model = ParentMixture(max_bits=2048)
        model.reset(b"\xff" * MAX_DONOR_BYTES)
        for _ in range(2048):
            model.predict(1)
            model.observe(1)
        state = model.export()
        self.assertEqual(int(state["donor_mass_hex"], 16), 65536**2048)
        self.assertLess(len(json.dumps(state)), 18000)
        self.assertEqual(len(model.state_digest()), 64)

    def test_pending_identity_causality_reset_and_invalid_truth(self):
        model = ParentMixture()
        model.reset(b"\xff")
        with self.assertRaises(ValueError):
            model.observe(1)
        model.predict(10000)
        pending = model.export()
        for q in (10000, 50000):
            with self.assertRaisesRegex(ValueError, "pending"):
                model.predict(q)
        with self.assertRaises(ValueError):
            model.reset(None)
        for bit in (-1, 2, True, None):
            with self.assertRaises(ValueError):
                model.observe(bit)
        self.assertEqual(model.export(), pending)
        model.observe(1)
        self.assertEqual(Fraction(int(model.export()["donor_mass_hex"], 16), int(model.export()["parent_mass_hex"], 16)),
                         Fraction(65536, 10000))
        model.reset(None)
        self.assertEqual(model.predict(199), 199)
        model.observe(0)

    def test_mixture_work_reset_donor_and_probability_bounds(self):
        for donor in (b"x" * 257, bytearray(b"x"), "x", 1):
            with self.assertRaises(ValueError):
                ParentMixture().reset(donor)
        for q in (0, 65536, True, None, 1.5):
            with self.assertRaises(ValueError):
                ParentMixture().predict(q)
        model = ParentMixture(max_bits=1)
        model.reset(b"a")
        model.predict(1)
        model.observe(1)
        model.reset(None)
        with self.assertRaisesRegex(ValueError, "bit budget"):
            model.predict(1)
        with self.assertRaisesRegex(ValueError, "reset budget"):
            model.reset(None)

    def test_full_coder_mixture_roundtrip_repeat_and_state(self):
        raw = b"a bounded donor value" * 8
        truth = bits(raw)
        probabilities = [1 + ((i * 509 + 32767) % 65535) for i in range(len(truth))]
        e, m = Encoder(max_bits=len(truth)), ParentMixture(max_bits=len(truth))
        m.reset(raw[:128])
        states = []
        for bit, q in zip(truth, probabilities):
            e.encode(bit, m.predict(q))
            m.observe(bit)
            states.append((e.low, e.high, m.state_digest()))
        payload = e.finish()
        d, n, repeat = Decoder(payload, max_bits=len(truth)), ParentMixture(max_bits=len(truth)), Encoder(max_bits=len(truth))
        n.reset(raw[:128])
        for expected, q, state in zip(truth, probabilities, states):
            mixed = n.predict(q)
            bit = d.decode(mixed)
            self.assertEqual(bit, expected)
            n.observe(bit)
            repeat.encode(bit, mixed)
            self.assertEqual((d.low, d.high, n.state_digest()), state)
        self.assertEqual(repeat.finish(), payload)


if __name__ == "__main__":
    unittest.main()
