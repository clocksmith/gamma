"""Synthetic exactness and bounded decoder checks; no corpus input is read."""
from __future__ import annotations

import bz2
import hashlib
import json
import os
from pathlib import Path
import random
import resource
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import causal_wordcode_fifo128_bz2_v1 as codec


def synthetic_populations():
    rng = random.Random("causal-wordcode-fifo128-design-v1")
    words = [bytes(rng.randrange(97, 123) for _ in range(14)) for _ in range(256)]
    reuse = b"".join(b"<page><title>" + words[i % 80] + b"</title><text>" +
                     b" ".join(words[rng.randrange(80)] for _ in range(15)) +
                     b"</text></page>\n" for i in range(60))
    return {"reuse": reuse, "eviction": b" ".join(words + words + list(reversed(words)))}


class CausalWordcodeTests(unittest.TestCase):
    def check_all(self, raw):
        parent = codec.parent_module()
        baseline = parent.compress(raw)
        states = []
        for arm in codec.ARMS:
            with self.subTest(arm=arm, raw_bytes=len(raw)):
                archive, encoded = codec.encode(raw, arm)
                restored, decoded = codec.decode(archive, arm)
                repeated, repeat_report = codec.repeat(raw, arm)
                self.assertEqual(raw, restored)
                self.assertEqual(archive, repeated)
                self.assertEqual(encoded, repeat_report)
                for key in ("state_digest", "transition_digest", "word_events", "occupied_slots",
                            "next_slot", "insertions", "evictions", "opcode_bytes", "references"):
                    self.assertEqual(encoded[key], decoded[key], key)
                self.assertEqual(encoded["complete_archive_bytes"], len(archive))
                self.assertEqual(encoded["framing_bytes"] + encoded["compressed_payload_bytes"], len(archive))
                self.assertEqual(encoded["raw_sha256"], hashlib.sha256(raw).hexdigest())
                self.assertIsNone(encoded["complete_package_bytes"])
                self.assertFalse(encoded["qualification_authority"])
                if arm in ("P", "K"):
                    self.assertEqual(archive, baseline)
                states.append((encoded["state_digest"], encoded["transition_digest"]))
        self.assertEqual(len(set(states)), 1)

    def test_empty_arbitrary_and_reserved_bytes(self):
        for raw in (b"", bytes(range(256)) * 2, b"\0\x01\x80\xff" * 8,
                    b"alphabet\x01alphabet\0alphabet\xffalphabet"):
            self.check_all(raw)

    def test_exact_case_whitespace_markup_entities_and_invalid_utf8(self):
        self.check_all(b'<x b="2" a="1">New York\r\nNEW YORK\nNew  York&amp;\xff\x00</x>\n'
                       b'<bad x="not closed\r\nALPHABET alphabet alphabet\x01')

    def test_word_boundaries_lengths_and_whole_words(self):
        raw = b" ".join(b"a" * n for n in (1, 4, 5, 32, 33, 100, 5, 32, 33))
        raw += b" alphabetalphabet alphabet alphabet alphabet2alphabet"
        self.check_all(raw)
        words = codec.Lexicon()
        for n in (4, 5, 32, 33):
            words.observe_word(b"x" * n, n)
        self.assertEqual(set(words.ids), {b"x" * 5, b"x" * 32})

    def test_fifo_wrap_hit_does_not_refresh_and_exact_eviction(self):
        words = [b"word" + bytes([65 + i // 26, 65 + i % 26]) for i in range(129)]
        lex = codec.Lexicon()
        for i, word in enumerate(words[:128]):
            lex.observe_word(word, (i + 1) * 7)
        self.assertEqual(lex.next_slot, 0)
        lex.observe_word(words[0], 903)
        self.assertEqual(lex.next_slot, 0)
        lex.observe_word(words[128], 910)
        self.assertNotIn(words[0], lex.ids)
        self.assertEqual(lex.slots[0], words[128])
        self.assertEqual(lex.evictions, 1)
        raw = b" ".join(words + words[:2] + list(reversed(words)))
        self.check_all(raw)

    def test_literal_control_has_no_references_but_identical_states(self):
        data = b"alphabet alphabet alphabet"
        packed, report = codec.pack_words(data)
        literal, control = codec.pack_words(data, references=False)
        self.assertEqual(packed, b"alphabet \x01\x01 \x01\x01")
        self.assertEqual(literal, data)
        self.assertEqual(report["references"], 2)
        self.assertEqual(control["references"], 0)
        self.assertEqual(report["state_digest"], control["state_digest"])
        self.assertEqual(report["transition_digest"], control["transition_digest"])

    def test_unknown_truncated_and_adjacent_references_rejected(self):
        for data in (b"\x01", b"\x01\x01", b"\x01\xff", b"alphabet\x01\x01",
                     b"alphabet \x01\x01\x01\x01", b"alphabet \x01\x01extra"):
            with self.subTest(data=data), self.assertRaises(codec.CodecError):
                codec.unpack_words(data)
        with self.assertRaisesRegex(codec.CodecError, "forbidden"):
            codec.unpack_words(b"alphabet \x01\x01", references=False)

    def test_bzip2_truncation_checksum_trailing_and_expansion_rejected(self):
        body = bz2.compress(b"alphabet " * 30, 9)
        for bad in (body[:-1], body + b"extra", body + body, b"garbage"):
            with self.subTest(length=len(bad)), self.assertRaises(codec.CodecError):
                codec.inflate(bad, 4096)
        changed = bytearray(body)
        changed[-5] ^= 128
        with self.assertRaises(codec.CodecError):
            codec.inflate(bytes(changed), 4096)
        with self.assertRaisesRegex(codec.CodecError, "expansion"):
            codec.inflate(bz2.compress(b"x" * 4097), 4096)

    def test_parent_dictionary_and_opcode_validation(self):
        for raw in (b"", b"\x41", b"\x01\x20short", b"\0\x01", b"\0\x80"):
            with self.subTest(raw=raw), self.assertRaises(codec.CodecError):
                codec.unpack_parent_words(raw)
        parent = codec.parent_module()
        for raw in (b"\0", b"\0\xfe"):
            with self.assertRaises(codec.CodecError):
                codec.undo_opcodes(raw, parent)
        with patch.object(codec, "MAX_OPCODE", 50), self.assertRaisesRegex(codec.CodecError, "bound"):
            codec.unpack_parent_words(b"\x01\x20" + b"a" * 32 + b"\x80\x80")
        with patch.object(codec, "MAX_RAW", 5), self.assertRaisesRegex(codec.CodecError, "bound"):
            codec.undo_opcodes(b"\0\x01", parent)

    def test_hard_input_and_each_expansion_bound(self):
        with self.assertRaises(codec.CodecError):
            codec.encode(b"x" * (codec.MAX_RAW + 1))
        with self.assertRaises(codec.CodecError):
            codec.decode(b"x" * (codec.MAX_ARCHIVE + 1))
        with self.assertRaises(codec.CodecError):
            codec.pack_words(b"x" * (codec.MAX_OPCODE + 1))
        with self.assertRaises(codec.CodecError):
            codec.unpack_words(b"x" * (codec.MAX_PACKED + 1))
        with patch.object(codec, "MAX_OPCODE", 15), self.assertRaisesRegex(codec.CodecError, "bound"):
            codec.unpack_words(b"alphabet \x01\x01")

    def test_exact_maximum_raw_input(self):
        raw = b"\0" * codec.MAX_RAW
        archive, encoded = codec.encode(raw, "T")
        restored, decoded = codec.decode(archive)
        self.assertEqual(raw, restored)
        self.assertEqual(encoded["opcode_bytes"], codec.MAX_OPCODE)
        self.assertEqual(encoded["state_digest"], decoded["state_digest"])

    def test_arm_mismatch_unknown_header_and_noncanonical_opcode_rejected(self):
        parent, _ = codec.encode(b"alphabet alphabet", "P")
        causal, _ = codec.encode(b"alphabet alphabet", "T")
        for archive, arm in ((parent, "T"), (causal, "P"), (causal, "L"), (b"wrong", None)):
            with self.assertRaises(codec.CodecError):
                codec.decode(archive, arm)
        with self.assertRaisesRegex(codec.CodecError, "noncanonical opcode"):
            codec.decode(b"OWF1t" + bz2.compress(b"<page>"))

    def test_parent_source_identity_is_mandatory(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "parent.py"
            path.write_bytes(b"raise RuntimeError('must not execute')")
            with patch.object(codec, "PARENT_PATH", path), self.assertRaisesRegex(codec.CodecError, "identity"):
                codec.encode(b"fixture")

    def test_synthetic_gain_and_eviction_loss_are_both_retained(self):
        for name, raw in synthetic_populations().items():
            p, _ = codec.encode(raw, "P")
            t, report = codec.encode(raw, "T")
            self.assertEqual(codec.decode(t)[0], raw)
            self.assertEqual(codec.repeat(raw, "T")[0], t)
            self.assertGreater(report["references"], 0)
            if name == "reuse":
                self.assertLess(len(t), len(p))
            else:
                self.assertGreater(len(t), len(p))
                self.assertGreater(report["evictions"], 0)

    def test_driver_api_p_k_identity_and_fresh_state(self):
        raw = b"alphabet alphabet\r\n"
        p = codec.compress_arm(raw, "P")
        k = codec.compress_arm(raw, "K")
        self.assertEqual(p, k)
        t = codec.compress_arm(raw, "T")
        encoded = codec.stats()
        self.assertEqual(codec.decompress_arm(t, "T"), raw)
        self.assertEqual(codec.stats()["state_digest"], encoded["state_digest"])
        codec.compress_arm(b"different bytes", "T")
        self.assertEqual(codec.compress_arm(raw, "T"), t)

    def test_independent_cli_encode_decode_repeat_and_no_overwrite(self):
        def limits():
            os.sched_setaffinity(0, {4})
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2,) * 2)
            resource.setrlimit(resource.RLIMIT_CPU, (30,) * 2)
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            source = directory / "input"
            raw = b'<page><title>Alphabet</title><text>Alphabet alphabet\xff\x01</text></page>\r\n' * 3
            source.write_bytes(raw)
            for arm in codec.ARMS:
                reports, archives = [], []
                for phase in ("encode", "decode", "repeat"):
                    output = directory / (arm + "." + phase)
                    input_path = directory / (arm + ".encode") if phase == "decode" else source
                    command = [sys.executable, str(Path(codec.__file__).resolve()), phase,
                               str(input_path), str(output), "--arm", arm]
                    result = subprocess.run(command, capture_output=True, text=True, timeout=60,
                                            preexec_fn=limits)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    reports.append(json.loads(result.stdout))
                    if phase == "decode":
                        self.assertEqual(output.read_bytes(), raw)
                    else:
                        archives.append(output.read_bytes())
                self.assertEqual(archives[0], archives[1])
                self.assertEqual(len({r["state_digest"] for r in reports}), 1)
                self.assertEqual(len({r["transition_digest"] for r in reports}), 1)
                before = output.read_bytes()
                refused = subprocess.run(command, capture_output=True, text=True, timeout=60,
                                         preexec_fn=limits)
                self.assertNotEqual(refused.returncode, 0)
                self.assertEqual(output.read_bytes(), before)
            self.assertFalse(list(directory.glob(".*")))

    def test_publish_rejects_racing_output_without_replacing_it(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "output"
            original_link = os.link
            def raced(source, target):
                path.write_bytes(b"another owner")
                original_link(source, target)
            with patch.object(codec.os, "link", side_effect=raced), self.assertRaises(FileExistsError):
                codec.publish(path, b"ours")
            self.assertEqual(path.read_bytes(), b"another owner")
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_relocated_local_source_closure_and_missing_parent_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tool = root / "tools/causal_wordcode_fifo128_bz2_v1.py"
            parent = root / "programs/opcode_word_bz2_v1/program.py"
            tool.parent.mkdir(parents=True)
            parent.parent.mkdir(parents=True)
            tool.write_bytes(Path(codec.__file__).read_bytes())
            parent.write_bytes(codec.PARENT_PATH.read_bytes())
            source = root / "input"
            raw = b"<page>alphabet alphabet\x01\x00</page>\r\n"
            source.write_bytes(raw)
            archive = root / "encoded"
            encoded = subprocess.run([sys.executable, str(tool), "encode", str(source), str(archive)],
                                     cwd=root, capture_output=True, text=True, timeout=60)
            self.assertEqual(encoded.returncode, 0, encoded.stderr)
            self.assertEqual(archive.read_bytes(), codec.encode(raw)[0])
            decoded = subprocess.run([sys.executable, str(tool), "decode", str(archive), str(root / "restored")],
                                     cwd=root, capture_output=True, text=True, timeout=60)
            self.assertEqual(decoded.returncode, 0, decoded.stderr)
            self.assertEqual((root / "restored").read_bytes(), raw)
            parent.unlink()
            rejected = subprocess.run([sys.executable, str(tool), "decode", str(archive), str(root / "missing")],
                                      cwd=root, capture_output=True, text=True, timeout=60)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertFalse((root / "missing").exists())


if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (30,) * 2)
    os.sched_setaffinity(0, {4})
    unittest.main()
