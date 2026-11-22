"""Public self-tests; no optimizer or existing checker is imported."""
from functools import lru_cache
import itertools
import json
import os
import random
import unittest

from check import (Frozen, Invalid, Language, check_job, claims, compact_sources, decode,
                   digest, dictionary, json_read, lower, row_objectives)


def serialized(value):
    return json.dumps(value).encode()


def uint(value):
    return value.to_bytes(4, "big")


def dictionary_bytes(entries):
    fields = [b"LTD1", uint(len(entries))]
    for entry in entries:
        raw = entry.encode()
        fields.extend((uint(len(raw)), raw))
    return b"".join(fields)


class Overlay:
    def __init__(self, original, base):
        self.original = original
        self.base = base
        self.blobs = {}

    def __call__(self, path):
        return self.blobs[path] if path in self.blobs else self.original(path)

    def get(self, name):
        return self(f"{self.base}/{name}")

    def put(self, name, data):
        self.blobs[f"{self.base}/{name}"] = data

    def manifest(self):
        return json_read(self.get("manifest.json"))

    def replace_dictionary(self, m, entries):
        raw = dictionary_bytes(entries)
        m["vocabulary"] = entries
        package = m["package"]
        package["entries"] = entries
        package["dictionary_bytes"] = len(raw)
        package["dictionary_sha256"] = key = digest(raw)
        package["package_bytes"] = len(raw) + package["packet_bytes"]
        self.put("dictionary.ltd", raw)
        for pid, metadata in package["programs"].items():
            name = f"packets/{pid}.ltv"
            packet = self.get(name)
            packet = packet[:5] + bytes.fromhex(key) + packet[37:]
            metadata["packet_sha256"] = digest(packet)
            self.put(name, packet)
        self.put("manifest.json", serialized(m))


class FrozenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.git = Frozen(os.environ.get("BITS_GAMMA", "."))
        cls.language = Language(compact_sources(cls.git))
        cls.stored = claims(cls.git)
        cls.size = cls.git.size("sixbit-v1/escape6_decoder.py")

    def check(self, job, overlay=None, claim=None):
        return check_job(overlay or self.git, self.language, job, self.stored[job] if claim is None
                         else claim, self.git.packet_ids, self.size)

    def test_all_and_report_semantics(self):
        cases = {
            "a-w-compact": (92, 92, True), "a-u-compact": (79, 79, True),
            "b-w-compact": (64, 64, True), "b-u-compact": (64, 64, True),
            "c-w-compact": (75925, 75925, True), "c-u-compact": (24166, 24613, False),
        }
        for job, expected in cases.items():
            with self.subTest(job=job):
                out = self.check(job)
                self.assertEqual(tuple(out[key] for key in ("bound", "witness", "tight")), expected)

    def test_changed_corpus_and_rehashed_metadata(self):
        modified = Overlay(self.git, "scale-v2")
        key = "generated/sources/0003-compact.js"
        raw = modified.get(key)
        raw = b"X" + raw[1:] if raw[:1] != b"X" else b"Y" + raw[1:]
        modified.put(key, raw)
        for name in ("generated/manifest.json", "qualification/report.json",
                     "qualification-rerun-v1/report.json"):
            m = json_read(modified.get(name))
            next(row for row in m["rows"] if (row["variant"], row["id"]) ==
                 ("compact", 3))["sha256"] = digest(raw)
            modified.put(name, serialized(m))
        with self.assertRaisesRegex(Invalid, "frozen source identity: 3"):
            compact_sources(modified, self.git)

    def test_slot_swap_with_coherent_dictionary_and_packet_hashes(self):
        job = "b-w-compact"
        modified = Overlay(self.git, f"sixbit-v1/run-v1/{job}")
        m = modified.manifest()
        slots = list(m["vocabulary"])
        slots[0], slots[1] = slots[1], slots[0]
        modified.replace_dictionary(m, slots)
        with self.assertRaisesRegex(Invalid, "decoded bytes differ"):
            self.check(job, modified)

    def test_ineligible_entry_with_coherent_dictionary_and_packet_hashes(self):
        job = "b-w-compact"
        modified = Overlay(self.git, f"sixbit-v1/run-v1/{job}")
        m = modified.manifest()
        modified.replace_dictionary(m, ["\u2603"] + m["vocabulary"][1:])
        with self.assertRaisesRegex(Invalid, "ineligible dictionary"):
            self.check(job, modified)

    def test_corrupt_escape_with_rehashed_packet(self):
        job = "c-w-compact"
        modified = Overlay(self.git, f"sixbit-v1/run-v1/{job}")
        m = modified.manifest()
        name = "packets/1005.lte"
        packet = modified.get(name)
        bits = "".join(f"{byte:08b}" for byte in packet[40:])
        # Before the first ESC, every token occupies exactly six bits.
        first = next(i for i in range(0, len(bits) - 13, 6) if bits[i:i + 6] == "111111")
        corrupt = bits[:first + 6] + "0000000" + bits[first + 13:]
        packet = packet[:40] + int(corrupt, 2).to_bytes(len(packet) - 40, "big")
        modified.put(name, packet)
        m["programs"]["1005"]["packet_sha256"] = digest(packet)
        modified.put("manifest.json", serialized(m))
        with self.assertRaisesRegex(Invalid, "invalid escaped ASCII"):
            self.check(job, modified)

    def test_inflated_claim(self):
        job = "a-w-compact"
        claim = dict(self.stored[job], min_entries_at_least=93)
        with self.assertRaisesRegex(Invalid, "claimed integer bound"):
            self.check(job, claim=claim)

    def test_specific_potential_change_invalidates_unchanged_claim(self):
        job = "a-w-compact"
        modified = Overlay(self.git, f"sixbit-v1/run-v1/{job}")
        cert = json_read(modified.get("certificate.json"))
        p = cert["potentials"]["3"]
        scale = cert["scale"]
        self.assertEqual(p[0], min(p))
        p[0] -= scale  # No positive outgoing rebates existed; precisely one unit is lost.
        modified.put("certificate.json", serialized(cert))
        self.assertEqual(lower(self.language, "A", "W", cert, 0), (91 * scale, scale))
        with self.assertRaisesRegex(Invalid, "claimed integer bound"):
            self.check(job, modified)


class TinyTests(unittest.TestCase):
    def test_exhaustive_weak_duality_and_tight_certificates(self):
        programs = {"1": "aa", "2": "ab"}
        language = Language(programs)
        expected = {"A": 2, "B": 1, "C": 36}  # B counts omissions in the minimization.
        tight = {
            "A": (1, 0, {"1": [0, 0, 0], "2": [2, 1, 0]}),
            "B": (1, 1, {"1": [1, 0, 0], "2": [1, 1, 0]}),
            "C": (3, 24, {"1": [58, 29, 0], "2": [74, 45, 0]}),
        }
        rng = random.Random(451)
        for rule in "WU":
            pieces = sorted({s[i:j] for s in programs.values()
                             for i in range(len(s)) for j in range(i + 1, len(s) + 1)
                             if language.allows(rule, s[i:j])})
            self.assertEqual(pieces, ["a", "b"])

            def brute(kind, budget):
                best = float("inf")
                for size in range(len(pieces) + 1):
                    if kind != "A" and size > budget:
                        continue
                    for words in itertools.combinations(pieces, size):
                        @lru_cache(None)
                        def cost(tail):
                            if not tail:
                                return 0
                            ways = [7 + cost(tail[len(w):]) for w in words if tail.startswith(w)]
                            if kind == "C":
                                ways.append(15 + cost(tail[1:]))
                            return min(ways, default=float("inf"))
                        costs = [cost(s) for s in programs.values()]
                        misses = costs.count(float("inf"))
                        objective = {"A": size if not misses else float("inf"),
                                     "B": misses, "C": sum(costs)}[kind]
                        best = min(best, objective)
                return best

            for kind in "ABC":
                budget = 0 if kind == "A" else 1
                optimum = brute(kind, budget)
                self.assertEqual(optimum, expected[kind])
                scale, mu, potentials = tight[kind]
                candidates = [(scale, mu, potentials)]
                candidates.extend((3, 0 if kind == "A" else rng.randrange(30),
                                   {pid: [rng.randrange(-50, 51) for _ in range(3)]
                                    for pid in programs}) for _ in range(100))
                for i, (scale, mu, potentials) in enumerate(candidates):
                    cert = {"scale": scale, "mu": mu, "kind": "B1" if kind == "B" else kind,
                            "potentials": potentials}
                    num, den = lower(language, kind, rule, cert, budget)
                    self.assertLessEqual(num, optimum * den)
                    if i == 0:
                        self.assertEqual(num, optimum * den)

    def test_distinct_problem_witness_and_whole_program_exclusion(self):
        lang = Language({"1": "ééxééz", "2": "yxz", "3": "éz", "4": "x"})
        self.assertFalse(lang.allows("W", "éé"))  # two positions, one problem
        self.assertTrue(lang.allows("U", "éé"))
        self.assertFalse(lang.allows("W", "éz"))
        self.assertFalse(lang.allows("U", "éz"))
        self.assertFalse(lang.allows("W", "x"))
        long = "é" * 81
        lang = Language({"1": long + "a", "2": long + "b"})
        self.assertTrue(lang.allows("W", long[:-1]))
        self.assertFalse(lang.allows("W", long))
        self.assertTrue(lang.allows("U", long))

    def test_packet_envelope_rejects_unused_ids_padding_and_extras(self):
        raw = dictionary_bytes(["a"])
        self.assertEqual(dictionary(raw), ["a"])
        key = digest(raw)
        header = b"LTV1\x06" + bytes.fromhex(key) + uint(1)
        self.assertEqual(decode(header + b"\0", ["a"], key, False), (b"a", 1, 0))
        for invalid in (header + b"\1", header + b"\4", header + b"\0\0", header):
            with self.assertRaises(Invalid):
                decode(invalid, ["a"], key, False)
        with self.assertRaises(Invalid):
            dictionary(raw + b"\0")

    def test_integer_boundary_no_float_rounding(self):
        scale = 1 << 60
        result = row_objectives("A", 80, 78 * scale + 1, scale, 79, 80, 0,
                                {"min_entries_at_least": 79})
        self.assertEqual((result["bound"], result["tight"]), (79, True))


if __name__ == "__main__":
    unittest.main()
