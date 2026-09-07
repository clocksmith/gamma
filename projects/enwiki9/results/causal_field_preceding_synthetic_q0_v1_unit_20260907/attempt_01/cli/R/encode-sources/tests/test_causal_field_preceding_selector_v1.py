#!/usr/bin/env python3
"""Synthetic selector proofs and an explicitly non-production framed test codec.

The test format fixes parent Q16=32768. Its 81-byte header carries mode, raw
and modeled lengths, raw and dictionary SHA256, and payload length. Dictionary
JSON is an external decoder input counted separately. P and K share mode zero.
No decoder process receives the synthetic raw or modeled encoder input.
"""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import struct
import subprocess
import sys
import time
from types import ModuleType
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import causal_field_preceding_selector_v1 as subject

CODER_PATH = ROOT / "tools/causal_field_parent_coder_v1.py"
CODER_HASH = "6c6f8311b6fda0bbf5fdbd0a45a52ea9f145ebc1fe9d506e1af1923478d5abb8"
coder_source = CODER_PATH.read_bytes()
if hashlib.sha256(coder_source).hexdigest() != CODER_HASH:
    raise ValueError("frozen parent coder source changed")
coder = ModuleType("preceding_test_frozen_coder")
exec(compile(coder_source, str(CODER_PATH), "exec"), coder.__dict__)
base, wrt = subject.base, subject.base.wrt
HEADER = struct.Struct(">4sBII32s32sI")
MODE = {"P": 0, "K": 0, "T": 1, "O": 2, "R": 3, "S": 4}
MAX_MODELED = 4 * subject.MAX_RAW + 4096
MAX_ARCHIVE = HEADER.size + 16 * MAX_MODELED + 1
RETAIN = Path(os.environ["GAMMA_PRECEDING_RETAIN"]) if os.environ.get("GAMMA_PRECEDING_RETAIN") else None
SEPARATING = (b"{{t|id=A|kind=x|v=mmmmmmmm}}{{t|id=B|kind=y|v=nnnnnnnn}}"
              b"{{t|id=C|kind=x|v=mmmmmmmm}}")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def code(*values):
    return bytes(wrt.wrt_byte_transform(value) for value in values)


def literals(raw):
    return b"".join(code(wrt.ESCAPE, byte) if byte >= 128 or byte in
                    (wrt.ESCAPE, wrt.CAPITALIZED, wrt.UPPERCASE, wrt.END_UPPER)
                    else code(byte) for byte in raw)


def token(index):
    if index < 80:
        return code(128 + index)
    if index < 3920:
        index -= 80
        return code(0xD0 + index // 80, 0x80 + index % 80)
    index -= 3920
    return code(0xF0 + index // 2560, 0xD0 + index // 80 % 32, 0x80 + index % 80)


def feed(adapter, modeled):
    return b"".join(adapter.feed(byte) for byte in modeled)


def dictionary_bytes(words):
    return canonical([word.hex() for word in words])


def reference(modeled, words, raw_bytes):
    stored = b"\0" * 5 + b"\7" + raw_bytes.to_bytes(4, "big") + modeled
    return wrt.parse_store_bytes(stored, list(words)).decoded


class Machine:
    """Common causal bit state; decoding also checks native encoder intervals."""
    def __init__(self, arm, words, raw_bytes, modeled_bytes, payload=None):
        self.adapter = subject.Adapter(words, arm, raw_bytes)
        self.arm = arm
        self.bits = modeled_bytes * 8
        self.encoder = coder.Encoder(max_bits=self.bits)
        self.decoder = None if payload is None else coder.Decoder(payload, max_bits=self.bits)
        self.mixture = coder.ParentMixture(max_bits=self.bits)
        self.activation = None
        self.raw, self.modeled, self.probabilities, self.states = (bytearray() for _ in range(4))
        self.changed = self.interval_checks = 0

    def byte(self, value=None):
        result = 0
        for shift in range(7, -1, -1):
            if self.activation != self.adapter.activation_id:
                self.mixture.reset(self.adapter.donor if self.arm in "TORS" else None)
                self.activation = self.adapter.activation_id
            q = self.mixture.predict(32768)
            self.probabilities.extend(struct.pack(">H", q))
            self.changed += q != 32768
            bit = self.decoder.decode(q) if self.decoder is not None else (value >> shift) & 1
            self.encoder.encode(bit, q)
            if self.decoder is not None:
                base.require((self.decoder.low, self.decoder.high, self.decoder.bit_count) ==
                             (self.encoder.low, self.encoder.high, self.encoder.bit_count),
                             "decoder/encoder common arithmetic state differs")
                self.interval_checks += 1
            self.mixture.observe(bit)
            result = (result << 1) | bit
        self.modeled.append(result)
        emission = self.adapter.feed(result)
        self.raw.extend(emission)
        state = {"adapter": self.adapter.state_digest(), "mixture": self.mixture.export(),
                 "activation": self.activation, "coder": [self.encoder.low, self.encoder.high,
                    self.encoder.bit_count, sha(bytes(self.encoder._output))]}
        self.states.extend(hashlib.sha256(canonical(state)).digest())
        return emission

    def finish(self):
        stats = self.adapter.finish()
        payload = self.encoder.finish()
        if self.decoder is not None:
            base.require(payload == self.decoder.payload, "noncanonical arithmetic payload")
        return payload, {"policy": subject.POLICY, "arm": self.arm, "parent_q16": 32768,
            "raw_bytes": len(self.raw), "raw_sha256": sha(self.raw),
            "modeled_bytes": len(self.modeled), "modeled_sha256": sha(self.modeled),
            "probability_sha256": sha(self.probabilities), "state_chain_sha256": sha(self.states),
            "probability_count": len(self.probabilities) // 2, "state_boundaries": len(self.states) // 32,
            "changed_probability_bits": self.changed, "adapter": stats,
            "mixture": self.mixture.export(), "coder": [self.encoder.low, self.encoder.high,
                self.encoder.bit_count], "payload_sha256": sha(payload), "payload_bytes": len(payload),
            "frame_bytes": HEADER.size, "archive_bytes": HEADER.size + len(payload),
            "dictionary_input_bytes": len(dictionary_bytes(self.adapter.words)),
            "decoder_arm_option_bytes": 1,
            "decoder_arm_scope": "Explicit one-byte test option; K bookkeeping is not identified by the shared P/K frame",
            "complete_package_bytes": None, "full_corpus_score": None, "corpus_bytes": 0}


def encode(modeled, words, raw_bytes, arm):
    base.require(type(raw_bytes) is int and 0 <= raw_bytes <= subject.MAX_RAW, "raw input exceeds synthetic bound")
    base.require(isinstance(modeled, bytes) and 1 <= len(modeled) <= 4 * raw_bytes + 4096,
                 "modeled input exceeds bound")
    machine = Machine(arm, words, raw_bytes, len(modeled))
    raw = reference(modeled, words, raw_bytes)
    for byte in modeled:
        machine.byte(byte)
    payload, report = machine.finish()
    base.require(machine.raw == raw, "independent raw inverse differs")
    header = HEADER.pack(b"CFP1", MODE[arm], raw_bytes, len(modeled), hashlib.sha256(raw).digest(),
                         hashlib.sha256(dictionary_bytes(words)).digest(), len(payload))
    return header + payload, machine, report


def decode(archive, words, arm):
    base.require(isinstance(archive, bytes) and HEADER.size < len(archive) <= MAX_ARCHIVE,
                 "archive length exceeds framing bound")
    magic, mode, raw_bytes, modeled_bytes, raw_hash, dictionary_hash, payload_bytes = HEADER.unpack_from(archive)
    base.require(magic == b"CFP1" and mode == MODE[arm], "frame magic or mode differs")
    base.require(raw_bytes <= subject.MAX_RAW and 1 <= modeled_bytes <= 4 * raw_bytes + 4096,
                 "framed raw or modeled work exceeds bound")
    base.require(dictionary_hash == hashlib.sha256(dictionary_bytes(words)).digest(), "dictionary differs")
    base.require(1 <= payload_bytes <= 16 * modeled_bytes + 1 and
                 len(archive) == HEADER.size + payload_bytes, "payload framing differs")
    machine = Machine(arm, words, raw_bytes, modeled_bytes, archive[HEADER.size:])
    for _ in range(modeled_bytes):
        machine.byte()
    payload, report = machine.finish()
    base.require(hashlib.sha256(machine.raw).digest() == raw_hash, "decoded raw digest differs")
    base.require(reference(bytes(machine.modeled), words, raw_bytes) == machine.raw,
                 "independent WRT inverse differs")
    return bytes(machine.raw), machine, report


def source_rows():
    paths = [ROOT / row["path"] for row in subject.source_inventory()]
    paths.extend([CODER_PATH, Path(__file__)])
    return [{"path": str(path.relative_to(ROOT)), "bytes": len(path.read_bytes()),
             "sha256": sha(path.read_bytes())} for path in sorted(paths)]


def retain_sources(directory):
    directory.mkdir(parents=True, exist_ok=False)
    rows = source_rows()
    for row in rows:
        path = directory / row["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / row["path"]).read_bytes())
    (directory / "inventory.json").write_bytes(canonical(rows))
    return rows


def child_limits():
    os.sched_setaffinity(0, {4})
    resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_FSIZE, (33554432, 33554432))
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.alarm(120)


def worker():
    # Synthetic-only child interface; the decoder has no raw/modeled input path.
    operation, arm, input_path, dictionary_path, output_path, raw_count = sys.argv[2:]
    child_limits()
    out = Path(output_path)
    out.mkdir(exist_ok=False)
    start, cpu = time.monotonic(), time.process_time()
    words = [bytes.fromhex(word) for word in json.loads(Path(dictionary_path).read_bytes())]
    data = Path(input_path).read_bytes()
    if operation == "encode":
        archive, machine, report = encode(data, words, int(raw_count), arm)
        (out / "archive.bin").write_bytes(archive)
    else:
        base.require(operation == "decode" and raw_count == "-", "invalid decoder interface")
        raw, machine, report = decode(data, words, arm)
        (out / "inverse.raw").write_bytes(raw)
        (out / "inverse.modeled").write_bytes(machine.modeled)
    (out / "probabilities.q16").write_bytes(machine.probabilities)
    (out / "states.sha256").write_bytes(machine.states)
    (out / "result.json").write_bytes(canonical(report))
    (out / "resources.json").write_bytes(canonical({"wall_seconds": time.monotonic() - start,
        "cpu_seconds": time.process_time() - cpu, "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "cpu_set": sorted(os.sched_getaffinity(0)), "interval_checks": machine.interval_checks,
        "decoder_inputs": [input_path, dictionary_path] if operation == "decode" else None}))


class SelectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checks = {"per_byte_old_policy_equalities": 0, "future_prefix_boundaries": 0,
                      "cli_phases": [], "separating": None}

    @classmethod
    def tearDownClass(cls):
        if RETAIN is not None:
            (RETAIN / "checks.json").write_bytes(canonical(cls.checks))

    def test_01_source_identity_and_synthetic_bounds(self):
        self.assertLessEqual((ROOT / "tools/causal_field_preceding_selector_v1.py").stat().st_size, 16384)
        self.assertLessEqual(Path(__file__).stat().st_size, 32768)
        self.assertEqual(sha(CODER_PATH.read_bytes()), CODER_HASH)
        self.assertEqual(sha((ROOT / "tools/causal_field_wrt_adapter_v1.py").read_bytes()), subject.BASE_SHA256)
        for bound in (-1, 8193, True, 1.0):
            with self.assertRaises(ValueError):
                subject.Adapter([], raw_limit=bound)
        for arm in ("", "TT", "X", 1):
            with self.assertRaises(ValueError):
                subject.Adapter([], arm)

    def test_02_two_field_behavior_equals_old_policy_at_every_byte(self):
        modeled = b"\7" + literals(b"{{t|kind=x|v=mmm}}{{t|kind=y|v=nnn}}{{t|kind=x|v=mmm}}")
        raw_len = len(modeled) - 1
        for arm in "PKTORS":
            original = base.Adapter([], "T" if arm == "O" else arm, raw_len)
            original.arm = arm  # Explicit comparator name only; old lookup remains exact.
            candidate = subject.Adapter([], arm, raw_len)
            for byte in modeled:
                self.assertEqual(candidate.feed(byte), original.feed(byte))
                self.assertEqual(base.Adapter.state_digest(candidate), original.state_digest())
                self.assertNotEqual(candidate.state_digest(), original.state_digest())
                self.checks["per_byte_old_policy_equalities"] += 1
            self.assertEqual(candidate.finish()["raw_sha256"], original.finish()["raw_sha256"])

    def test_03_separating_three_field_donors_and_adjacent_tables(self):
        prefix = b"\7" + literals(SEPARATING[:-10])
        expected = {"P": None, "K": literals(b"mmmmmmmm"), "T": literals(b"mmmmmmmm"),
                    "O": None, "R": literals(b"nnnnnnnn"), "S": literals(b"nnnnnnnn")}
        observations = {}
        for arm in "PKTORS":
            adapter = subject.Adapter([], arm, len(SEPARATING))
            self.assertEqual(feed(adapter, prefix), SEPARATING[:-10])
            self.assertEqual(adapter.donor, expected[arm])
            self.assertEqual(adapter.completed_invocations, 0 if arm == "P" else 2)
            if arm in "KTRS":
                self.assertEqual(adapter.serial, 4)
                self.assertIn((b"t", b"kind", b"x", b"v"), adapter.table)
                self.assertNotIn((b"t", b"id", b"A", b"v"), adapter.table)
            observations[arm] = {"donor": None if adapter.donor is None else adapter.donor.hex(),
                                 "state_digest": adapter.state_digest(), "table": adapter.table_rows()}
            feed(adapter, literals(SEPARATING[-10:]))
            adapter.finish()
        self.checks["separating"] = observations

    def test_04_changed_previous_key_has_no_exact_fallback(self):
        seed = b"{{t|id=A|kind=x|v=mmm}}{{t|id=A|other=x|v="
        for arm, expected in (("T", None), ("O", literals(b"mmm")), ("R", literals(b"mmm")), ("S", None)):
            adapter = subject.Adapter([], arm)
            feed(adapter, b"\7" + literals(seed))
            self.assertEqual(adapter.donor, expected)

    def test_05_future_value_and_malformed_suffix_prefix_is_identical(self):
        common = b"\7" + literals(SEPARATING[:-10])
        suffixes = [b"mmmmmmmm}}", b"nnnnnnnn}}", b"|id=duplicate}}", b"{{nested|v=x}}}}", b"x" * 65 + b"}}", b""]
        for arm in "PKTORS":
            baseline = None
            for suffix in suffixes:
                machine = Machine(arm, [], 8192, MAX_MODELED)
                for byte in common:
                    machine.byte(byte)
                snapshot = (bytes(machine.probabilities), bytes(machine.states), machine.adapter.state_digest(),
                            machine.mixture.state_digest(), machine.encoder.low, machine.encoder.high)
                if baseline is None:
                    baseline = snapshot
                self.assertEqual(snapshot, baseline)
                self.checks["future_prefix_boundaries"] += len(common)
                serial = machine.adapter.serial
                for byte in literals(suffix):
                    machine.byte(byte)
                self.assertEqual(machine.adapter.serial, serial + (2 if suffix in suffixes[:2] and arm != "P" else 0))

    def test_06_commit_waits_for_valid_close_and_never_partial_invalid(self):
        prefixes = [b"{{t|id=A|kind=x|v=mmm", b"{{t|id=A|kind=x|v=mmm}"]
        malformed = [b"{{t|id=A|kind=x|v=mmm|id=duplicate}}", b"{{t|id=A|kind=x|v={{u|z=x}}}}",
                     b"{{t|id=A|kind=x|v=" + b"x" * 65 + b"}}", b"{{t|id=A|kind=x|v=mmm}x}}",
                     b"{{" + b"n" * 33 + b"|id=A|v=mmm}}"]
        for raw in prefixes + malformed:
            for arm in "KTORS":
                adapter = subject.Adapter([], arm, len(raw))
                self.assertEqual(feed(adapter, b"\7" + literals(raw)), raw)
                self.assertEqual(adapter.serial, 0)
                self.assertEqual(len(adapter.table), 0)
                self.assertEqual(adapter.completed_invocations, 0)
                adapter.finish()

    def test_07_fifo128_overwrite_does_not_refresh_order(self):
        records = [b"{{t|id=" + str(index).encode() + b"|kind=" + str(index).encode() + b"|v=m}}"
                   for index in range(65)]
        raw = b"".join(records[:64]) + records[0] + records[64]
        for arm in "KTRS":
            adapter = subject.Adapter([], arm, len(raw))
            self.assertEqual(feed(adapter, b"\7" + literals(b"".join(records[:64]))), b"".join(records[:64]))
            self.assertEqual(len(adapter.table), 128)
            first = list(adapter.table)[:2]
            feed(adapter, literals(records[0]))
            self.assertEqual(list(adapter.table)[:2], first)
            feed(adapter, literals(records[64]))
            self.assertTrue(all(ident not in adapter.table for ident in first))
            self.assertEqual((adapter.completed_invocations, adapter.serial, adapter.evictions), (66, 132, 2))
            adapter.finish()

    def test_08_capitalization_entry_compatibility_and_rotated_requirements(self):
        words = [b"alpha", b"beta", b"gamma"]
        def entry(ident, kind, capitalized=False):
            value = literals(b"{{t|id=" + ident + b"|kind=" + kind + b"|v")
            return value + (code(wrt.CAPITALIZED, wrt.ESCAPE, 61) if capitalized else literals(b"="))
        seed = b"\7" + entry(b"A", b"x") + token(0) + literals(b"}}")
        seed += entry(b"B", b"y", True) + token(1) + literals(b"}}")
        seed += entry(b"C", b"z", True) + token(2) + literals(b"}}")
        for arm, kind, wanted in (("T", b"x", None), ("R", b"x", token(2)),
                                  ("S", b"x", None), ("S", b"y", token(2))):
            adapter = subject.Adapter(words, arm)
            feed(adapter, seed + entry(b"D", kind, True))
            self.assertEqual(adapter.wrt_state(), (False, True))
            self.assertEqual(adapter.donor, wanted)
            if arm == "T":
                self.assertEqual(adapter.incompatible_lookups, 1)

    def test_09_event_alignment_previous_and_target_are_both_required(self):
        cases = [([b"kind=x"], literals(b"{{t|id=A|") + token(0) + literals(b"|v=mmm}}")),
                 ([b"x|"], literals(b"{{t|id=A|kind=") + token(0) + literals(b"v=mmm}}")),
                 ([b"v=mmm"], literals(b"{{t|id=A|kind=x|") + token(0) + literals(b"}}")),
                 ([b"mmm|"], literals(b"{{t|id=A|kind=x|v=") + token(0) + literals(b"last=z}}"))]
        for words, record in cases:
            adapter = subject.Adapter(words)
            feed(adapter, b"\7" + record)
            self.assertNotIn((b"t", b"kind", b"x", b"v"), adapter.table)
            self.assertGreater(adapter.unaligned_values, 0)
        # An unaligned first field does not veto a later aligned adjacent pair.
        words = [b"id=A"]
        adapter = subject.Adapter(words)
        feed(adapter, b"\7" + literals(b"{{t|") + token(0) + literals(b"|kind=x|v=mmm}}"))
        self.assertIn((b"t", b"kind", b"x", b"v"), adapter.table)

    def test_10_zero_output_controls_donor_cap_and_modeled_cap(self):
        value = code(wrt.CAPITALIZED) + token(0) + code(wrt.END_UPPER)
        prefix = literals(b"{{t|id=A|kind=x|v=")
        adapter = subject.Adapter([b"alpha"])
        feed(adapter, b"\7" + prefix + value + literals(b"}}") + prefix)
        self.assertEqual(adapter.donor, value)
        adapter = subject.Adapter([])
        oversized = code(wrt.END_UPPER) * 257 + literals(b"x")
        feed(adapter, b"\7" + prefix + oversized + literals(b"}}"))
        self.assertEqual(adapter.oversized_donors, 1)
        self.assertNotIn((b"t", b"kind", b"x", b"v"), adapter.table)
        limited = subject.Adapter([], raw_limit=0)
        feed(limited, b"\7" + code(wrt.END_UPPER) * 4095)
        with self.assertRaisesRegex(ValueError, "modeled work bound"):
            limited.feed(code(wrt.END_UPPER)[0])
        self.assertTrue(limited.failed)
        with self.assertRaises(ValueError):
            limited.feed(7)

    def test_11_all_arms_framed_codec_exact_probability_and_state_roundtrips(self):
        modeled = b"\7" + literals(SEPARATING)
        archives, reports = {}, {}
        for arm in "PKTORS":
            archive, encoded, report = encode(modeled, [], len(SEPARATING), arm)
            raw, decoded, inverse = decode(archive, [], arm)
            repeat, repeated, repeat_report = encode(bytes(decoded.modeled), [], len(raw), arm)
            self.assertEqual(raw, SEPARATING)
            self.assertEqual(archive, repeat)
            self.assertEqual(report, inverse)
            self.assertEqual(report, repeat_report)
            self.assertEqual(encoded.probabilities, decoded.probabilities)
            self.assertEqual(encoded.states, decoded.states)
            self.assertEqual(decoded.interval_checks, len(modeled) * 8)
            archives[arm], reports[arm] = archive, report
        self.assertEqual(archives["P"], archives["K"])
        self.assertEqual(decode(archives["K"], [], "P")[0], SEPARATING)
        self.assertEqual(reports["P"]["probability_sha256"], reports["K"]["probability_sha256"])
        self.assertGreater(reports["T"]["changed_probability_bits"], 0)
        self.assertEqual(reports["O"]["changed_probability_bits"], 0)
        self.assertGreater(reports["R"]["changed_probability_bits"], 0)
        self.assertGreater(reports["S"]["changed_probability_bits"], 0)
        self.checks["synthetic_complete_costs"] = {arm: {key: row[key] for key in
            ("archive_bytes", "frame_bytes", "payload_bytes", "dictionary_input_bytes", "decoder_arm_option_bytes",
             "changed_probability_bits")}
            for arm, row in reports.items()}

    def test_12_nonempty_dictionary_and_multibyte_event_codec(self):
        words = [b"unused"] * 3921
        words[80], words[3920] = b"alpha", b"beta"
        one = literals(b"{{t|id=A|kind=x|v=") + token(80) + literals(b"}}")
        two = literals(b"{{t|id=B|kind=y|v=") + token(3920) + literals(b"}}")
        three = literals(b"{{t|id=C|kind=x|v=") + token(80) + literals(b"}}")
        modeled = b"\7" + one + two + three
        raw = b"{{t|id=A|kind=x|v=alpha}}{{t|id=B|kind=y|v=beta}}{{t|id=C|kind=x|v=alpha}}"
        for arm in "PKTORS":
            archive, encoded, report = encode(modeled, words, len(raw), arm)
            inverse, decoded, inverse_report = decode(archive, words, arm)
            self.assertEqual(inverse, raw)
            self.assertEqual(report, inverse_report)
            self.assertEqual(encoded.states, decoded.states)
            self.assertEqual(report["dictionary_input_bytes"], len(dictionary_bytes(words)))

    def test_13_malformed_archive_rejects_lengths_mode_dictionary_and_payload(self):
        archive, _, _ = encode(b"\7" + literals(SEPARATING), [], len(SEPARATING), "T")
        cases = [archive[:HEADER.size], archive[:-1], archive + b"\0"]
        fields = list(HEADER.unpack_from(archive))
        for index, value in ((0, b"BAD!"), (1, 0), (2, 8193), (3, 0), (3, MAX_MODELED + 1),
                             (4, b"\0" * 32), (5, b"\0" * 32), (6, 0)):
            mutated = fields.copy()
            mutated[index] = value
            cases.append(HEADER.pack(*mutated) + archive[HEADER.size:])
        for tail in (archive[HEADER.size:-1], archive[HEADER.size:] + b"\0"):
            mutated = fields.copy()
            mutated[6] = len(tail)
            cases.append(HEADER.pack(*mutated) + tail)
        for candidate in cases:
            with self.assertRaises(ValueError):
                decode(candidate, [], "T")
        with self.assertRaises(ValueError):
            decode(archive, [b"other"], "T")
        for invalid in (b"\7" + code(wrt.ESCAPE), b"\7" + token(0), b"\0"):
            with self.assertRaises((ValueError, IndexError)):
                encode(invalid, [], 0, "T")

    def test_14_independent_cli_archives_inverses_and_repeats(self):
        if RETAIN is None:
            self.skipTest("durable evidence directory required for independent child phases")
        tree = RETAIN / "cli"
        tree.mkdir(exist_ok=False)
        (tree / "input.raw").write_bytes(SEPARATING)
        (tree / "input.modeled").write_bytes(b"\7" + literals(SEPARATING))
        (tree / "dictionary.json").write_bytes(dictionary_bytes([]))
        for arm in "PKTORS":
            arm_root = tree / arm
            arm_root.mkdir()
            results = []
            for phase in ("encode", "decode", "repeat"):
                sources = retain_sources(arm_root / (phase + "-sources"))
                operation = "decode" if phase == "decode" else "encode"
                input_path = tree / "input.modeled" if phase == "encode" else arm_root / (
                    "encode/archive.bin" if phase == "decode" else "decode/inverse.modeled")
                command = [sys.executable, str(Path(__file__)), "--worker", operation, arm, str(input_path),
                           str(tree / "dictionary.json"), str(arm_root / phase),
                           "-" if phase == "decode" else str(len(SEPARATING))]
                receipt = {"command": command, "sources_before": sources, "input": str(input_path),
                    "input_bytes": input_path.stat().st_size, "input_sha256": sha(input_path.read_bytes()),
                    "dictionary_bytes": 2, "dictionary_sha256": sha(dictionary_bytes([])),
                    "scope": "synthetic-only", "corpus_bytes": 0}
                (arm_root / (phase + "-command.json")).write_bytes(canonical(receipt))
                start = time.monotonic()
                with (arm_root / (phase + ".log")).open("wb") as log:
                    process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=120,
                                             env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
                receipt.update({"returncode": process.returncode, "wall_seconds": time.monotonic() - start,
                                "sources_after": source_rows()})
                (arm_root / (phase + "-execution.json")).write_bytes(canonical(receipt))
                self.assertEqual(process.returncode, 0)
                self.assertEqual(receipt["sources_before"], receipt["sources_after"])
                self.checks["cli_phases"].append({"arm": arm, "phase": phase,
                    **json.loads((arm_root / phase / "resources.json").read_bytes())})
                results.append(json.loads((arm_root / phase / "result.json").read_bytes()))
            self.assertEqual(results[0], results[1])
            self.assertEqual(results[0], results[2])
            self.assertEqual((arm_root / "encode/archive.bin").read_bytes(), (arm_root / "repeat/archive.bin").read_bytes())
            self.assertEqual((arm_root / "decode/inverse.raw").read_bytes(), SEPARATING)
            self.assertEqual((arm_root / "decode/inverse.modeled").read_bytes(), (tree / "input.modeled").read_bytes())
            for name in ("probabilities.q16", "states.sha256"):
                self.assertEqual((arm_root / "encode" / name).read_bytes(), (arm_root / "decode" / name).read_bytes())
                self.assertEqual((arm_root / "encode" / name).read_bytes(), (arm_root / "repeat" / name).read_bytes())
        self.assertEqual((tree / "P/encode/archive.bin").read_bytes(), (tree / "K/encode/archive.bin").read_bytes())


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        worker()
    else:
        unittest.main(verbosity=2, failfast=True)
