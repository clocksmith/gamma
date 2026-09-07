"""Independent FIFO/count proof fixtures; synthetic inputs and no corpus reads."""
from collections import Counter
import copy
import hashlib
import itertools
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import causal_bucket_v2 as codec


def sha(data):
    return hashlib.sha256(data).hexdigest()


def direct_buckets(raw):
    groups = [bytes(value for before, value in zip(b"\0" + raw, raw) if before == key) for key in range(256)]
    return groups


def plain_archive(raw, frame_size):
    parts = [raw[i:i + frame_size] for i in range(0, len(raw), frame_size)]
    result = bytearray(codec.HEADER.pack(codec.PLAIN_MAGIC, frame_size, len(parts), len(raw)))
    for part in parts:
        compressed = zlib.compress(part, 9)
        result.extend(codec.FRAME.pack(len(part), 0, 0, 0, 0, len(compressed), 0, hashlib.sha256(part).digest()))
        result.extend(compressed)
    return bytes(result)


def selected_archive(raw, transformed):
    compressed = zlib.compress(transformed, 9)
    return (codec.HEADER.pack(codec.MAGIC, codec.MAX_FRAME, 1, len(raw))
            + codec.FRAME.pack(len(raw), 5, 0, 0, 0, len(compressed), 0, hashlib.sha256(raw).digest()) + compressed)


def common(report):
    report = copy.deepcopy(report)
    report.pop("mode", None)
    for frame in report["frames"]:
        frame.pop("comparison", None)
    return report


def walk():
    rng = random.Random(871)
    value, raw = 0, bytearray()
    for _ in range(8192):
        value = (value + rng.choice((-1, 0, 1))) & 255
        raw.append(value)
    return bytes(raw)


class IndependentBucketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = Path(tempfile.mkdtemp(prefix="causal_bucket_independent_"))

    def retain(self, name, value):
        (self.evidence / name).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")

    def test_exhaustive_ternary_fifo_and_histogram_identity(self):
        transcript = hashlib.sha256()
        count = raw_bytes = 0
        for length in range(9):
            for values in itertools.product((0, 1, 255), repeat=length):
                raw = bytes(values)
                groups = direct_buckets(raw)
                expected = bytes([raw[-1]]) + b"".join(groups) if raw else b""
                transformed = codec.transform(raw)
                self.assertEqual(transformed, expected)
                self.assertEqual(codec.inverse(transformed), raw)
                if raw:
                    self.assertEqual(Counter(raw), Counter(transformed[1:]))
                    self.assertEqual(codec.counts(transformed), list(map(len, groups)))
                transcript.update(bytes([length]) + raw + transformed)
                count += 1
                raw_bytes += length
        self.assertEqual(count, 9841)
        self.retain("exhaustive.json", dict(cases=count, cumulative_raw_bytes=raw_bytes,
            alphabet=[0, 1, 255], lengths=list(range(9)), transcript_sha256=transcript.hexdigest(),
            oracle="independent direct filtering by original predecessor; compared every queue count and FIFO inverse"))

    def test_endpoint_is_necessary_and_outer_checksum_disambiguates(self):
        left, right = b"\x01\x00\x01", b"\x01\x01\x00"
        a, b = codec.transform(left), codec.transform(right)
        self.assertEqual(a[1:], b[1:])
        self.assertNotEqual(a[0], b[0])
        self.assertEqual(codec.inverse(a), left)
        self.assertEqual(codec.inverse(b), right)
        good, malicious = selected_archive(left, a), selected_archive(left, b)
        self.assertEqual(codec.decode(good)[0], left)
        with self.assertRaisesRegex(ValueError, "raw checksum"):
            codec.decode(malicious)
        (self.evidence / "endpoint-good.d2g").write_bytes(good)
        (self.evidence / "endpoint-altered.d2g").write_bytes(malicious)
        self.retain("endpoint-collision.json", dict(left_hex=left.hex(), right_hex=right.hex(),
            same_bucket_payload_hex=a[1:].hex(), left_endpoint=a[0], right_endpoint=b[0],
            valid_alternate_inverse=True, outer_raw_checksum_rejected=True))

    def test_fifo_order_zeros_and_every_byte(self):
        cases = (b"", b"\0", b"\xff", b"\0" * 64, b"\0\xff\0", bytes(range(256)),
                 bytes(range(255, -1, -1)), b"\1\0\2\0\3\0\1\0\4")
        for raw in cases:
            with self.subTest(raw=raw.hex()):
                encoded = codec.transform(raw)
                self.assertEqual(codec.inverse(encoded), raw)
                if raw:
                    self.assertEqual(encoded[1:], b"".join(direct_buckets(raw)))

    def test_queue_underflow_negative_count_and_payload_bounds(self):
        # endpoint1 + payload10 has two entries in bucket0 but none in bucket1.
        for malformed in (b"\0", b"\1\0", b"\1\1\0"):
            with self.subTest(malformed=malformed.hex()), self.assertRaises(ValueError):
                codec.inverse(malformed)
        with patch.object(codec, "MAX_FRAME", 8):
            with self.assertRaises(ValueError):
                codec.transform(b"x" * 9)
            with self.assertRaises(ValueError):
                codec.inverse(b"\0" * 10)
        with self.assertRaises(ValueError):
            codec.counts(b"")

    def test_encoder_and_decoder_archive_caps_are_aligned(self):
        expected = plain_archive(b"x", 1)
        for mode in ("K", "D"):
            with patch.object(codec, "MAX_ARCHIVE", len(expected) - 1), self.assertRaises(ValueError):
                codec.encode(b"x", mode=mode, frame_size=1)
            with patch.object(codec, "MAX_ARCHIVE", len(expected)):
                encoded, _ = codec.encode(b"x", mode=mode, frame_size=1)
                self.assertEqual(encoded, expected)
                self.assertEqual(codec.decode(encoded)[0], b"x")
        self.retain("archive-cap.json", dict(raw_hex="78", frame_size=1, complete_archive_bytes=len(expected),
            lowered_rejection_cap=len(expected) - 1, exact_acceptance_cap=len(expected),
            unpatched_counterexample_description="121212 one-byte plain frames need8000016B, above MAX_ARCHIVE8000000B"))

    def test_complete_cost_selection_fallback_and_raw_repeats(self):
        raws = {"empty": b"", "walk": walk(), "fallback": random.Random(491).randbytes(2048),
                "mixed": walk()[:4096] + random.Random(491).randbytes(2048)}
        summaries = {}
        for name, raw in raws.items():
            frame_size = 4096 if name == "mixed" else 65536
            parent = plain_archive(raw, frame_size)
            (self.evidence / (name + ".raw")).write_bytes(raw)
            (self.evidence / (name + ".P.d2g")).write_bytes(parent)
            rows = []
            for mode in ("K", "D"):
                encoded, report = codec.encode(raw, mode, frame_size)
                restored, decoded = codec.decode(encoded)
                repeated, again = codec.encode(restored, mode, frame_size)
                self.assertEqual(restored, raw)
                self.assertEqual(encoded, repeated)
                self.assertEqual(report, again)
                self.assertEqual(common(report), decoded)
                self.assertEqual(report["archive_sha256"], sha(encoded))
                self.assertEqual(sum(report["costs"].values()), len(encoded))
                self.assertLessEqual(len(encoded), len(parent))
                if mode == "K":
                    self.assertEqual(encoded, parent)
                selected = 0
                for index, row in enumerate(report["frames"]):
                    part = raw[index * frame_size:(index + 1) * frame_size]
                    transformed = codec.transform(part)
                    p_size = codec.FRAME.size + len(zlib.compress(part, 9))
                    b_size = codec.FRAME.size + len(zlib.compress(transformed, 9))
                    chosen = mode == "D" and b_size < p_size
                    self.assertEqual(row["comparison"]["plain_bytes"], p_size)
                    self.assertEqual(row["comparison"]["bucket_bytes"], b_size)
                    self.assertEqual(row["comparison"]["selected"], chosen)
                    self.assertEqual(row["complete_frame_bytes"], b_size if chosen else p_size)
                    self.assertEqual(sum(row["costs"].values()), row["complete_frame_bytes"])
                    self.assertEqual(row["transmitted_payload_sha256"], sha(transformed if chosen else part))
                    selected += chosen
                if name == "walk" and mode == "D":
                    self.assertGreater(selected, 0)
                if name == "fallback":
                    self.assertEqual(encoded, parent)
                if name == "mixed" and mode == "D":
                    self.assertEqual([frame["mode"] for frame in report["frames"]], ["bucket", "plain"])
                for suffix, data in (("d2g", encoded), ("inverse", restored), ("repeat.d2g", repeated)):
                    (self.evidence / (name + "." + mode + "." + suffix)).write_bytes(data)
                self.retain(name + "." + mode + ".reports.json", dict(encode=report, decode=decoded, repeat=again))
                rows.append(dict(mode=mode, archive_bytes=len(encoded), selected_frames=selected))
            summaries[name] = dict(raw_bytes=len(raw), raw_sha256=sha(raw), frame_size=frame_size,
                                   parent_archive_bytes=len(parent), arms=rows)
        self.retain("roundtrips.json", summaries)

    def test_archive_framing_corruption_and_declared_output_limit(self):
        raw = b"\1\0\1"
        good = selected_archive(raw, codec.transform(raw))
        for malformed in (good[:7], good[:codec.HEADER.size], good[:-1], good + b"extra"):
            with self.subTest(bytes=len(malformed)), self.assertRaises(ValueError):
                codec.decode(malformed)
        with self.assertRaises(ValueError):
            codec.decode(good, max_output=2)
        wrong_frontend = codec.PLAIN_MAGIC + good[8:]
        with self.assertRaises(ValueError):
            codec.decode(wrong_frontend)
        wrong_payload_size = selected_archive(raw, codec.transform(raw) + b"\0")
        with self.assertRaises(ValueError):
            codec.decode(wrong_payload_size)


if __name__ == "__main__":
    unittest.main()
