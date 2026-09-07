#!/usr/bin/env python3
"""Synthetic-only event alignment and causality checks for the WRT adapter."""
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import causal_field_wrt_adapter_v1 as frontend

wrt = frontend.wrt


def code(*values):
    return bytes(wrt.wrt_byte_transform(value) for value in values)


def literals(raw):
    out = bytearray()
    for byte in raw:
        out.extend(code(wrt.ESCAPE, byte) if byte >= 128 or byte in (wrt.ESCAPE, wrt.CAPITALIZED, wrt.UPPERCASE, wrt.END_UPPER) else code(byte))
    return bytes(out)


def token(index):
    if index < 80:
        return code(128 + index)
    if index < 3920:
        index -= 80
        return code(0xD0 + index // 80, 0x80 + index % 80)
    index -= 3920
    return code(0xF0 + index // 2560, 0xD0 + index // 80 % 32, 0x80 + index % 80)


def prefix(name):
    return literals(b"{{place|name=" + name + b"|description=")


def record(name, value):
    return prefix(name) + value + literals(b"}}")


def reference(modeled, words):
    # Batch parsing is an independent synthetic oracle, never the adapter input.
    provisional = b"\7" + b"\0" * 4 + modeled
    state = wrt.WrtDecoderState()
    position, raw = 1, bytearray()
    while position < len(modeled):
        first = wrt.wrt_byte_transform(modeled[position])
        position += 1
        if first == wrt.ESCAPE:
            raw.extend(state.escaped(wrt.wrt_byte_transform(modeled[position])))
            position += 1
        elif first in (wrt.UPPERCASE, wrt.CAPITALIZED, wrt.END_UPPER):
            state.control(first)
        elif first >= 128:
            values = [first]
            if first > 0xCF:
                values.append(wrt.wrt_byte_transform(modeled[position]))
                position += 1
                if values[1] > 0xCF:
                    values.append(wrt.wrt_byte_transform(modeled[position]))
                    position += 1
            raw.extend(state.word(words[wrt.token_index(bytes(values))]))
        else:
            raw.extend(state.literal(first))
    stored = b"\0" * 5 + provisional[:1] + len(raw).to_bytes(4, "big") + modeled
    parsed = wrt.parse_store_bytes(stored, words)
    assert parsed.decoded == raw and stored[10:] == modeled
    return bytes(raw), parsed


def feed(adapter, modeled):
    return b"".join(adapter.feed(byte) for byte in modeled)


class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retained = Path(os.environ["GAMMA_FIELD_WRT_RETAIN"]) if os.environ.get("GAMMA_FIELD_WRT_RETAIN") else None
        if cls.retained is not None:
            cls.retained.mkdir(exist_ok=False)

    def test_flag_is_not_an_uppercase_control(self):
        adapter = frontend.Adapter([b"alpha"], raw_limit=5)
        self.assertEqual(adapter.feed(7), b"")
        self.assertEqual(adapter.wrt_state(), (False, False))
        self.assertEqual(adapter.feed(token(0)[0]), b"alpha")
        self.assertEqual(adapter.finish()["event_counts"], {"token": 1})
        for bad in (0, 6, 64, 255):
            with self.assertRaisesRegex(ValueError, "transform flag"):
                frontend.Adapter([], raw_limit=0).feed(bad)

    def test_multibyte_token_and_escape_release_only_complete_events(self):
        words = [b"unused"] * 3921
        words[80], words[3920] = b"second", b"third"
        adapter = frontend.Adapter(words, raw_limit=12)
        adapter.feed(7)
        for index, expected in ((80, b"second"), (3920, b"third")):
            values = token(index)
            for byte in values[:-1]:
                self.assertEqual(adapter.feed(byte), b"")
            self.assertEqual(adapter.feed(values[-1]), expected)
        self.assertEqual(adapter.feed(code(wrt.ESCAPE)[0]), b"")
        self.assertEqual(adapter.feed(code(255)[0]), b"\xff")
        adapter.finish()

    def test_control_literal_and_arbitrary_byte_reference(self):
        modeled = b"\7" + literals(bytes(range(256))) + code(wrt.UPPERCASE) + literals(b"alpha ")
        modeled += code(wrt.CAPITALIZED) + token(0) + code(wrt.END_UPPER)
        expected, parsed = reference(modeled, [b"beta"])
        adapter = frontend.Adapter([b"beta"], raw_limit=len(expected))
        emissions = []
        for position, byte in enumerate(modeled):
            output = adapter.feed(byte)
            emissions.append(output)
            matching = [event for event in parsed.events if event.end - 5 == position + 1]
            self.assertEqual(output, matching[0].decoded if matching else b"")
        self.assertEqual(b"".join(emissions), expected)
        adapter.finish()

    def test_conditional_recency_and_rotated_exact_donor_spans(self):
        words = [b"alpha", b"beta"]
        seed = b"\7" + record(b"A", token(0)) + record(b"B", token(1))
        modeled = seed + prefix(b"A") + token(0) + literals(b"}}")
        expected, _ = reference(modeled, words)
        tables = []
        for arm in "PKTRS":
            adapter = frontend.Adapter(words, arm, len(expected))
            beginning = seed + prefix(b"A")
            output = feed(adapter, beginning)
            wanted = None if arm == "P" else token(0) if arm in "KT" else token(1)
            self.assertEqual(adapter.donor, wanted)
            activation = adapter.activation_id
            output += feed(adapter, token(0) + literals(b"}}"))
            self.assertEqual(output, expected)
            if arm != "P":
                self.assertGreater(adapter.activation_id, activation)
                self.assertIsNone(adapter.donor)
                tables.append(adapter.table_digest)
                row = adapter.table[(b"place", b"name", b"A", b"description")]
                self.assertEqual(modeled[row["wrt_start"]:row["wrt_end"]], row["encoded"])
                self.assertEqual(expected[row["raw_start"]:row["raw_end"]], row["raw"])
            adapter.finish()
        self.assertEqual(len(set(tables)), 1)

    def test_zero_emission_controls_inside_value_belong_to_donor(self):
        value = code(wrt.CAPITALIZED) + token(0) + code(wrt.END_UPPER)
        modeled = b"\7" + record(b"A", value) + prefix(b"A") + value + literals(b"}}")
        expected, _ = reference(modeled, [b"alpha"])
        adapter = frontend.Adapter([b"alpha"], raw_limit=len(expected))
        beginning = b"\7" + record(b"A", value) + prefix(b"A")
        output = feed(adapter, beginning)
        self.assertEqual(adapter.donor, value)
        output += feed(adapter, value + literals(b"}}"))
        self.assertEqual(output, expected)
        adapter.finish()

    def test_capitalized_state_survives_escaped_equal_and_blocks_donor(self):
        words = [b"alpha"]
        seed = b"\7" + record(b"A", code(wrt.CAPITALIZED) + token(0))
        entry = literals(b"{{place|name=A|description") + code(wrt.CAPITALIZED, wrt.ESCAPE, ord("="))
        modeled = seed + entry + token(0) + literals(b"}}")
        expected, _ = reference(modeled, words)
        adapter = frontend.Adapter(words, raw_limit=len(expected))
        output = feed(adapter, seed + entry)
        self.assertEqual(adapter.wrt_state(), (False, True))
        self.assertIsNone(adapter.donor)
        self.assertEqual(adapter.incompatible_lookups, 1)
        output += feed(adapter, token(0) + literals(b"}}"))
        self.assertEqual(output, expected)
        row = adapter.table[(b"place", b"name", b"A", b"description")]
        self.assertEqual(row["encoded"], token(0))
        self.assertEqual(row["entry_state"], (False, True))
        adapter.finish()

    def test_R_and_S_filter_incompatible_entry_states(self):
        words = [b"alpha", b"beta", b"gamma"]
        def capitalized_entry(name):
            return literals(b"{{place|name=" + name + b"|description") + code(wrt.CAPITALIZED, wrt.ESCAPE, ord("="))
        seed = b"\7" + record(b"A", token(0)) + capitalized_entry(b"B") + token(1) + literals(b"}}")
        seed += capitalized_entry(b"C") + token(2) + literals(b"}}")
        for arm, name, wanted in (("T", b"A", None), ("R", b"A", token(2)), ("S", b"A", None), ("S", b"B", token(2))):
            adapter = frontend.Adapter(words, arm, raw_limit=8192)
            feed(adapter, seed + capitalized_entry(name))
            self.assertEqual(adapter.donor, wanted)

    def test_future_suffix_counterfactual_has_identical_prefix_states(self):
        words = [b"alpha", b"beta"]
        common = b"\7" + record(b"A", token(0)) + record(b"B", token(1)) + prefix(b"A")
        suffixes = [token(0) + literals(b"}}"), token(0) + literals(b"|name=duplicate}}"),
                    literals(b"{{nested|name=x|description=poison}}}}"), literals(b"x" * 65 + b"}}"), b""]
        for arm in "KTRS":
            traces = []
            for suffix in suffixes:
                adapter = frontend.Adapter(words, arm, raw_limit=8192)
                trace = []
                for byte in common:
                    emission = adapter.feed(byte)
                    trace.append((emission, adapter.donor, adapter.activation_id, adapter.state_digest()))
                feed(adapter, suffix)
                self.assertEqual(adapter.completed_invocations, 3 if suffix == suffixes[0] else 2)
                self.assertEqual(adapter.serial, 3 if suffix == suffixes[0] else 2)
                traces.append(trace)
            self.assertTrue(all(trace == traces[0] for trace in traces))

    def test_unaligned_value_start_or_end_never_installs_a_donor(self):
        # Caller-supplied synthetic opaque dictionary entries deliberately span syntax.
        for words, invocation in (([b"description=alpha"], literals(b"{{place|name=A|") + token(0) + literals(b"}}")),
                                  ([b"alpha|"], prefix(b"A") + token(0) + literals(b"last=z}}"))):
            modeled = b"\7" + invocation
            expected, _ = reference(modeled, words)
            adapter = frontend.Adapter(words, raw_limit=len(expected))
            self.assertEqual(feed(adapter, modeled), expected)
            self.assertNotIn((b"place", b"name", b"A", b"description"), adapter.table)
            self.assertGreater(adapter.unaligned_values, 0)
            adapter.finish()

    def test_invalid_duplicate_nested_and_overlong_invocations(self):
        cases = [record(b"A", literals(b"alpha|name=duplicate")),
                 prefix(b"A") + literals(b"{{nested|name=B|description=poison}}}}"),
                 prefix(b"A") + literals(b"x" * 2050 + b"{{nested|a=b|c=d}}}}"),
                 literals(b"{{" + b"x" * 33 + b"|a=b|c=d}}"),
                 literals(b"{{t|" + b"k" * 33 + b"=v|c=d}}"),
                 literals(b"{{t" + b"".join(b"|k" + str(i).encode() + b"=v" for i in range(9)) + b"}}")]
        for invocation in cases:
            modeled = b"\7" + invocation + record(b"after", literals(b"valid"))
            expected, _ = reference(modeled, [])
            adapter = frontend.Adapter([], raw_limit=len(expected))
            self.assertEqual(feed(adapter, modeled), expected)
            self.assertEqual(adapter.completed_invocations, 1)
            self.assertEqual(adapter.rejected_invocations, 1)
            self.assertEqual(len(adapter.table), 1)
            adapter.finish()

    def test_encoded_donor_bound_includes_control_bytes(self):
        value = code(wrt.END_UPPER) * 257 + literals(b"alpha")
        modeled = b"\7" + record(b"A", value)
        expected, _ = reference(modeled, [])
        adapter = frontend.Adapter([], raw_limit=len(expected))
        self.assertEqual(feed(adapter, modeled), expected)
        self.assertFalse(adapter.table)
        self.assertEqual(adapter.oversized_donors, 1)
        adapter.finish()

    def test_FIFO_capacity_and_replacement_do_not_refresh_insertion_order(self):
        modeled = b"\7" + b"".join(record(str(i).encode(), literals(b"v")) for i in range(130))
        modeled += record(b"2", literals(b"replacement")) + record(b"new", literals(b"v"))
        expected, _ = reference(modeled, [])
        self.assertLessEqual(len(expected), 8192)
        adapter = frontend.Adapter([], raw_limit=len(expected))
        self.assertEqual(feed(adapter, modeled), expected)
        self.assertEqual(len(adapter.table), 128)
        self.assertEqual(adapter.evictions, 3)
        self.assertEqual(next(iter(adapter.table))[2], b"3")
        adapter.finish()

    def test_malformed_WRT_output_and_work_bounds_fail_closed(self):
        for tail in (code(0xD0, 0), code(0xD0, 0xD0), code(0xF0, 0xF0), code(0xF0, 0xD0, 0), token(0)):
            adapter = frontend.Adapter([], raw_limit=8)
            with self.assertRaises(ValueError):
                feed(adapter, b"\7" + tail)
            self.assertTrue(adapter.failed)
            with self.assertRaisesRegex(ValueError, "failed"):
                adapter.feed(0)
        adapter = frontend.Adapter([b"too-long"], raw_limit=1)
        with self.assertRaisesRegex(ValueError, "raw length"):
            feed(adapter, b"\7" + token(0))
        adapter = frontend.Adapter([], raw_limit=0)
        with self.assertRaisesRegex(ValueError, "modeled work"):
            feed(adapter, b"\7" + code(wrt.END_UPPER) * adapter.modeled_limit)

    def test_finish_rejects_incomplete_events_or_wrong_raw_length(self):
        for modeled in (b"", b"\7" + code(wrt.ESCAPE), b"\7" + code(0xD0), b"\7" + code(0xF0, 0xD0)):
            adapter = frontend.Adapter([], raw_limit=0)
            feed(adapter, modeled)
            with self.assertRaisesRegex(ValueError, "flag or incomplete"):
                adapter.finish()
        adapter = frontend.Adapter([], raw_limit=1)
        adapter.feed(7)
        with self.assertRaisesRegex(ValueError, "raw length"):
            adapter.finish()
        adapter.feed(literals(b"x")[0])
        first = adapter.finish()
        self.assertEqual(adapter.finish(), first)
        with self.assertRaisesRegex(ValueError, "closed"):
            adapter.feed(0)

    def test_source_closure_and_dictionary_identity(self):
        inventory = frontend.source_inventory()
        self.assertEqual(len(inventory), 3)
        for row in inventory:
            name = Path(row["path"]).name
            if name in frontend.PINS:
                self.assertEqual(row["sha256"], frontend.PINS[name])
        a, b = frontend.Adapter([b"ab", b"c"]), frontend.Adapter([b"a", b"bc"])
        self.assertNotEqual(a.dictionary_digest, b.dictionary_digest)
        for invalid in ([(b"x") * (frontend.MAX_RAW + 1)], [b""], [bytearray(b"x")]):
            with self.assertRaises(ValueError):
                frontend.Adapter(invalid)

    def test_repeated_event_replay_and_retained_synthetic_evidence(self):
        words = [b"alpha", b"beta"]
        modeled = b"\7" + record(b"A", code(wrt.CAPITALIZED) + token(0)) + record(b"B", token(1))
        modeled += record(b"A", code(wrt.CAPITALIZED) + token(0))
        expected, _ = reference(modeled, words)
        records = []
        started, cpu = time.monotonic(), time.process_time()
        for arm in "PKTRS":
            previous = None
            for repeat in range(2):
                adapter = frontend.Adapter(words, arm, len(expected))
                trace, raw = [], bytearray()
                for byte in modeled:
                    raw.extend(adapter.feed(byte))
                    trace.append({"modeled_bytes": adapter.modeled_count, "raw_bytes": adapter.raw_count,
                                  "activation_id": adapter.activation_id, "donor": None if adapter.donor is None else adapter.donor.hex(),
                                  "state_digest": adapter.state_digest()})
                stats = adapter.finish()
                self.assertEqual(raw, expected)
                if previous is not None:
                    self.assertEqual((stats, trace), previous)
                previous = stats, trace
                records.append({"arm": arm, "repeat": repeat, "stats": stats})
                if self.retained is not None:
                    (self.retained / (arm + "-" + str(repeat) + ".json")).write_text(json.dumps({"stats": stats, "trace": trace}, indent=2) + "\n")
                    (self.retained / (arm + "-" + str(repeat) + ".raw")).write_bytes(raw)
        if self.retained is not None:
            (self.retained / "synthetic.modeled").write_bytes(modeled)
            (self.retained / "synthetic.raw").write_bytes(expected)
            (self.retained / "dictionary.json").write_text(json.dumps([word.hex() for word in words]) + "\n")
            receipt = {"synthetic_only": True, "raw_bytes": len(expected), "modeled_bytes": len(modeled), "records": records,
                "source_files": frontend.source_inventory(), "cpu_seconds": time.process_time() - cpu,
                "wall_seconds": time.monotonic() - started, "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "affinity": sorted(os.sched_getaffinity(0)), "address_limit": resource.getrlimit(resource.RLIMIT_AS),
                "cpu_limit": resource.getrlimit(resource.RLIMIT_CPU), "complete_package_bytes": None,
                "qualification_authority": False, "corpus_bytes": 0}
            (self.retained / "receipt.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    unittest.main()
