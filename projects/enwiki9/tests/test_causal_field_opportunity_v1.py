"""Synthetic observation-only tests; no corpus, coder or probability inputs."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import causal_field_opportunity_v1 as opportunity

base = opportunity.base
wrt = base.wrt
SYNTHETIC_EVIDENCE = []


def code(*values):
    return bytes(wrt.wrt_byte_transform(value) for value in values)


def literals(raw):
    result = bytearray()
    for byte in raw:
        result.extend(code(wrt.ESCAPE, byte) if byte >= 128 or byte in
                      (wrt.ESCAPE, wrt.CAPITALIZED, wrt.UPPERCASE, wrt.END_UPPER) else code(byte))
    return bytes(result)


def token(index):
    assert 0 <= index < 80
    return code(128 + index)


def prefix(selector, *, template=b"t", first_key=b"s", later_key=b"v"):
    return literals(b"{{" + template + b"|" + first_key + b"=" + selector + b"|" + later_key + b"=")


def record(selector, value=b"x", **kwargs):
    return prefix(selector, **kwargs) + literals(value) + literals(b"}}")


class OpportunityTests(unittest.TestCase):
    def assert_parity(self, modeled, words=(), *, finish=True, arms="PKTRS", raw_limit=None):
        # This first baseline pass sizes an entirely synthetic fixture. The
        # observed adapter only ever receives one modeled byte at a time.
        sizing = base.Adapter(words, "P", 8192)
        raw = b"".join(sizing.feed(byte) for byte in modeled)
        self.assertLessEqual(len(raw), 8192)
        limit = len(raw) if raw_limit is None else raw_limit
        rows, states = {}, {}
        for arm in arms:
            expected = base.Adapter(words, arm, limit)
            observed = opportunity.Adapter(words, arm, limit, first_event_limit=8)
            self.assertEqual(expected.state_digest(), observed.state_digest())
            output = bytearray()
            for offset, byte in enumerate(modeled):
                left, right = expected.feed(byte), observed.feed(byte)
                self.assertEqual(left, right, (arm, offset))
                output.extend(right)
                self.assertEqual(expected.state_digest(), observed.state_digest(), (arm, offset))
                self.assertEqual(expected.donor, observed.donor, (arm, offset))
                self.assertEqual(expected.activation_id, observed.activation_id, (arm, offset))
            self.assertEqual(bytes(output), raw)
            if finish:
                self.assertEqual(expected.finish(), observed.finish())
            before = observed.state_digest()
            row = observed.diagnostics()
            self.assertEqual(observed.state_digest(), before)
            self.assertEqual(expected.state_digest(), before)
            self.assertEqual(sum(row["eligibility"].values()), row["start_values"])
            for group in ("conditional", "recency", "rotated"):
                self.assertEqual(sum(row[group].values()), row["eligibility"]["eligible"])
            self.assertEqual(row["inherited_selected_starts"], expected.selected_values)
            self.assertLessEqual(len(row["first_events"]), 8)
            self.assertEqual(len(row["first_events"]) + row["omitted_events"],
                             row["start_values"] + row["parser_invalidation_transitions"])
            if arm == "P":
                self.assertEqual(row["start_values"], 0)
                self.assertEqual(row["parser_invalidation_transitions"], 0)
                self.assertFalse(row["parser_enabled"])
            rows[arm], states[arm] = row, observed
        SYNTHETIC_EVIDENCE.append({"test": self.id(), "modeled_bytes": len(modeled),
            "modeled_sha256": hashlib.sha256(modeled).hexdigest(), "raw_bytes": len(raw),
            "raw_sha256": hashlib.sha256(raw).hexdigest(), "arms": list(arms),
            "every_modeled_byte_parity_checks": len(modeled) * len(arms), "diagnostics": rows})
        return rows, states

    def test_unique_first_values_allow_recency_without_conditional_hit(self):
        rows, _ = self.assert_parity(b"\7" + record(b"A") + record(b"B") + record(b"C"))
        self.assertEqual(rows["T"]["conditional"]["no_matching_template"], 1)
        self.assertEqual(rows["T"]["conditional"]["no_exact_first_value"], 2)
        self.assertEqual(rows["T"]["inherited_selected_starts"], 0)
        self.assertEqual(rows["R"]["inherited_selected_starts"], 2)
        self.assertEqual(rows["S"]["rotated"]["no_exact_tuple"], 3)

    def test_repeated_selector_allows_T_and_rotated_alternative(self):
        rows, _ = self.assert_parity(b"\7" + record(b"A", b"x") + record(b"B", b"y") + record(b"A", b"x"))
        for arm in "KT":
            self.assertEqual(rows[arm]["inherited_selected_starts"], 1)
        self.assertEqual(rows["T"]["conditional"]["exact_compatible_hit"], 1)
        self.assertEqual(rows["S"]["inherited_selected_starts"], 1)
        self.assertEqual(rows["S"]["rotated"]["compatible_rotated_hit"], 1)

    def test_exact_match_without_rotated_alternative_is_distinct(self):
        rows, _ = self.assert_parity(b"\7" + record(b"A") * 2)
        self.assertEqual(rows["T"]["inherited_selected_starts"], 1)
        self.assertEqual(rows["S"]["inherited_selected_starts"], 0)
        self.assertEqual(rows["S"]["rotated"]["missing_rotated_alternatives"], 1)

    def test_changed_template_later_key_and_first_key_partition_misses(self):
        for kwargs, wanted in (({"template": b"other"}, "no_matching_template"),
                               ({"later_key": b"other"}, "no_template_later_key"),
                               ({"first_key": b"other"}, "no_template_first_key_later_key")):
            with self.subTest(wanted=wanted):
                rows, _ = self.assert_parity(b"\7" + record(b"A") + record(b"A", **kwargs))
                self.assertEqual(rows["T"]["conditional"][wanted], 2 if wanted == "no_matching_template" else 1)
                self.assertEqual(rows["T"]["inherited_selected_starts"], 0)
                self.assertEqual(rows["R"]["inherited_selected_starts"], int("first_key" in kwargs))

    def test_incompatible_capitalization_after_escaped_equal(self):
        seed = prefix(b"A") + code(wrt.CAPITALIZED) + token(0) + literals(b"}}")
        later = literals(b"{{t|s=A|v") + code(wrt.CAPITALIZED, wrt.ESCAPE, ord("="))
        rows, states = self.assert_parity(b"\7" + seed + later + token(0) + literals(b"}}"), [b"alpha"])
        for arm in "KTRS":
            self.assertEqual(rows[arm]["conditional"]["incompatible_wrt_entry_state"], 1)
            self.assertEqual(rows[arm]["rotated"]["incompatible_exact_entry_state"], 1)
            self.assertEqual(rows[arm]["recency"]["no_compatible_wrt_entry_state"], 1)
            self.assertEqual(rows[arm]["inherited_selected_starts"], 0)
        self.assertEqual(states["T"].incompatible_lookups, 1)

    def test_zero_emission_controls_and_exact_encoded_donors_are_preserved(self):
        value = code(wrt.CAPITALIZED) + token(0) + code(wrt.END_UPPER)
        invocation = prefix(b"A") + value + literals(b"}}")
        rows, states = self.assert_parity(b"\7" + invocation * 2, [b"alpha"])
        self.assertEqual(rows["T"]["conditional"]["exact_compatible_hit"], 1)
        self.assertEqual(states["T"].table[(b"t", b"s", b"A", b"v")]["encoded"], value)

    def test_unaligned_entry_and_first_completed_span_are_separate(self):
        cases = (([b"v=alpha"], literals(b"{{t|s=A|") + token(0) + literals(b"}}"), "unaligned_entry"),
                 ([b"s=A|"], literals(b"{{t|") + token(0) + literals(b"v=alpha}}"), "unaligned_first_span"))
        for words, invocation, reason in cases:
            with self.subTest(reason=reason):
                rows, _ = self.assert_parity(b"\7" + invocation, words)
                self.assertEqual(rows["T"]["eligibility"][reason], 1)
                self.assertEqual(rows["T"]["inherited_selected_starts"], 0)

    def test_invalid_nested_and_overlong_are_transitions_without_guessed_causes(self):
        cases = (prefix(b"A") + literals(b"x|s=duplicate}}"),
                 prefix(b"A") + literals(b"{{n|a=b|c=d}}}}"),
                 prefix(b"A") + literals(b"x" * 2100 + b"{{n}}}}"),
                 literals(b"{{" + b"n" * 33 + b"|s=A|v=x}}"))
        for invalid in cases:
            rows, states = self.assert_parity(b"\7" + invalid + record(b"after"))
            for arm in "KTRS":
                self.assertEqual(rows[arm]["parser_invalidation_transitions"], 1)
                self.assertEqual(states[arm].rejected_invocations, 1)
                self.assertEqual(states[arm].completed_invocations, 1)
                event = next(row for row in rows[arm]["first_events"] if row["kind"] == "parser_invalidation")
                self.assertNotEqual(event["context"]["mode"], "invalid")
                self.assertNotIn("cause", event)
                self.assertLessEqual(event["context"]["invocation_bytes"], 2049)

    def test_EOF_incompleteness_does_not_invent_rejection(self):
        for tail in (b"{", b"{{t|s=A|v=unfinished"):
            rows, states = self.assert_parity(b"\7" + literals(tail))
            self.assertTrue(rows["T"]["end_state"]["finished"])
            self.assertTrue(rows["T"]["end_state"]["parser_prefix_incomplete"])
            self.assertFalse(rows["T"]["end_state"]["wrt_event_incomplete"])
            self.assertEqual(states["T"].rejected_invocations, 0)
            self.assertEqual(rows["T"]["parser_invalidation_transitions"], 0)

    def test_future_suffix_cannot_change_prefix_diagnostics_or_state(self):
        common = b"\7" + record(b"A") + record(b"B", b"y") + prefix(b"A")
        suffixes = (literals(b"x}}"), literals(b"x|s=duplicate}}"),
                    literals(b"{{nested}}}}"), literals(b"x" * 65 + b"}}"), b"")
        for arm in "PKTRS":
            prefixes = []
            for suffix in suffixes:
                expected = base.Adapter([], arm, 8192)
                observed = opportunity.Adapter([], arm, 8192)
                trace = []
                for byte in common + suffix:
                    self.assertEqual(expected.feed(byte), observed.feed(byte))
                    self.assertEqual(expected.state_digest(), observed.state_digest())
                    if observed.modeled_count <= len(common):
                        trace.append((observed.state_digest(), observed.diagnostics()))
                prefixes.append(trace)
            self.assertTrue(all(row == prefixes[0] for row in prefixes))

    def test_FIFO_eviction_and_invalidated_unaligned_span_preserve_state(self):
        modeled = b"\7" + b"".join(record(str(i).encode()) for i in range(130)) + record(b"0")
        rows, states = self.assert_parity(modeled)
        self.assertEqual(states["T"].evictions, 3)
        self.assertEqual(rows["T"]["conditional"]["no_exact_first_value"], 130)
        self.assertEqual(rows["T"]["inherited_selected_starts"], 0)
        # A start inside an opaque event is counted even if invalidation occurs
        # before finish_field, where the frozen unaligned_values counter lives.
        invocation = literals(b"{{t|s=A|") + token(0) + literals(b"}}")
        rows, states = self.assert_parity(b"\7" + invocation, [b"v={{nested}}"])
        self.assertEqual(rows["T"]["eligibility"]["unaligned_entry"], 1)
        self.assertEqual(rows["T"]["parser_invalidation_transitions"], 1)
        self.assertEqual(states["T"].unaligned_values, 0)

    def test_diagnostics_are_bounded_detached_and_do_not_override_state_methods(self):
        self.assertIs(opportunity.Adapter.state_digest, base.Adapter.state_digest)
        self.assertIs(opportunity.Adapter.stats, base.Adapter.stats)
        self.assertIs(opportunity.Adapter.feed, base.Adapter.feed)
        self.assertIs(opportunity.Adapter.finish, base.Adapter.finish)
        for invalid in (-1, 129, True, 1.5):
            with self.assertRaises(ValueError):
                opportunity.Adapter([], raw_limit=0, first_event_limit=invalid)
        for limit in (0, 1, 128):
            adapter = opportunity.Adapter([], raw_limit=8192, first_event_limit=limit)
            for byte in b"\7" + record(b"A") * 10:
                adapter.feed(byte)
            digest = adapter.state_digest()
            first = adapter.diagnostics()
            self.assertLessEqual(len(first["first_events"]), limit)
            self.assertLess(len(json.dumps(first)), 262144)
            first["eligibility"]["eligible"] = -1
            first["first_events"].append({"mutated": True})
            self.assertNotEqual(first, adapter.diagnostics())
            self.assertEqual(digest, adapter.state_digest())

    def test_malformed_WRT_and_output_bounds_keep_exact_failure_state(self):
        for modeled, words, limit in ((b"\7" + code(0xD0, 0), [], 8),
                                     (b"\7" + token(0), [], 8),
                                     (b"\7" + token(0), [b"too-long"], 1)):
            for arm in "PKTRS":
                expected = base.Adapter(words, arm, limit)
                observed = opportunity.Adapter(words, arm, limit)
                for byte in modeled:
                    failures = []
                    for adapter in (expected, observed):
                        try:
                            failures.append((None, adapter.feed(byte)))
                        except ValueError as error:
                            failures.append((str(error), None))
                    self.assertEqual(failures[0], failures[1])
                    self.assertEqual(expected.state_digest(), observed.state_digest())
                self.assertTrue(observed.failed)
        expected, observed = base.Adapter([], raw_limit=0), opportunity.Adapter([], raw_limit=0)
        for byte in b"\7" + code(wrt.ESCAPE):
            self.assertEqual(expected.feed(byte), observed.feed(byte))
        self.assertTrue(observed.diagnostics()["end_state"]["wrt_event_incomplete"])
        for adapter in (expected, observed):
            with self.assertRaises(ValueError):
                adapter.finish()
        self.assertEqual(expected.state_digest(), observed.state_digest())

    def test_pin_rejects_changed_adapter_and_inventory_is_only_four_sources(self):
        rows = opportunity.source_inventory()
        self.assertEqual(len(rows), 4)
        self.assertEqual({Path(row["path"]).name for row in rows},
                         {"causal_field_opportunity_v1.py", "causal_field_wrt_adapter_v1.py",
                          "causal_field_dependency_v1.py", "wrt_exact.py"})
        for row in rows:
            self.assertEqual(hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest(), row["sha256"])
        with patch.object(Path, "read_bytes", return_value=b"tampered"):
            with self.assertRaisesRegex(ValueError, "frozen WRT adapter source changed"):
                opportunity._load_adapter()


if __name__ == "__main__":
    unittest.main()
