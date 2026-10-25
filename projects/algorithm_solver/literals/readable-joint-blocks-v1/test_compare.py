"""Focused mechanism tests. No candidate program or protected corpus execution."""
from __future__ import annotations

import copy
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import compare


class LiteralComparisonTests(unittest.TestCase):
    def test_existing_alphabet_is_printable_ascii_and_lf(self):
        policy = compare.verify_alphabet_policy()
        self.assertEqual(policy["entries"], 96)
        self.assertEqual(set(policy["codepoints"]), set(range(32, 127)) | {10})
        self.assertNotIn("\t", compare.ALPHABET)
        self.assertNotIn("\r", compare.ALPHABET)

    def test_no_hidden_character_escape(self):
        for text in ("a\tb", "a\rb", "a\x00b", "caf\u00e9"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                compare.fit_dictionary({"a": text}, 128)

    def test_pool_small_blocks_need_distinct_owners(self):
        texts = {"a": "shared one\nshared two\nprivate a\n",
                 "b": "shared one\nshared two\nprivate b\n"}
        pool = compare.candidate_pool(texts)
        self.assertIn("shared one\nshared two\n", pool)
        self.assertIn("private a\n", pool)
        self.assertNotIn("shared two\nprivate a\n", pool)
        self.assertFalse(set(texts.values()) & set(pool))
        self.assertTrue(all(len(x.splitlines()) <= 3 and len(x.encode()) <= 256 for x in pool))

    def test_repetition_within_one_source_does_not_count_as_reuse(self):
        pool = compare.candidate_pool({"a": "a\nb\na\nb\n", "b": "different\n"})
        self.assertNotIn("a\nb\n", pool)

    def test_whole_sources_and_cross_variant_bans(self):
        pool = compare.candidate_pool({"a": "first\nsecond\n", "b": "first\nthird\n"}, ["first\n"])
        self.assertNotIn("first\n", pool)
        self.assertNotIn("first\nsecond\n", pool)
        self.assertNotIn("first\nthird\n", pool)

    def test_exact_minimum_beats_longest_match_greedy(self):
        vocabulary = ["a", "b", "c", "d", "ab", "abc", "cd"]
        sequence = compare.scorer.shortest_encode("abcd", vocabulary)
        self.assertEqual(sequence, [4, 6])
        parsed, missing = compare.codec.parse(b"abcd", [s.encode() for s in vocabulary])
        self.assertEqual(parsed, sequence)
        self.assertEqual(missing, [])

    def test_minimum_count_matches_exhaustive_short_strings(self):
        words = ["a", "b", "aa", "ab", "ba", "bb", "aba"]
        for text in ("".join(p) for n in range(1, 6) for p in itertools.product("ab", repeat=n)):
            for chosen in ([], ["aa"], ["ab", "ba"], ["aa", "bb", "aba"]):
                edges = [[] for _ in text]
                for piece in chosen:
                    for start, end in compare.occurrence_ends(text, piece).items():
                        edges[start].append(end)
                for optional in words[2:]:
                    actual = compare.minimum_count(len(text), edges, compare.occurrence_ends(text, optional))
                    expected = len(compare.scorer.shortest_encode(text, list(dict.fromkeys(["a", "b"] + chosen + [optional]))))
                    self.assertEqual(actual, expected, (text, chosen, optional))

    def test_canonical_tie_uses_lower_dictionary_id(self):
        self.assertEqual(compare.scorer.shortest_encode("aaa", ["a", "aa"]), [0, 1])
        self.assertEqual(compare.scorer.shortest_encode("aaa", ["aa", "a"]), [0, 1])

    def test_fit_deterministic_under_input_order(self):
        texts = {"a": "shared one\nshared two\nunique a\n",
                 "b": "shared one\nshared two\nunique b\n"}
        for capacity in (128, 256):
            first, report = compare.fit_dictionary(texts, capacity)
            second, again = compare.fit_dictionary(dict(reversed(list(texts.items()))), capacity)
            self.assertEqual(first, second)
            self.assertEqual(report["trace"], again["trace"])
            self.assertEqual(first[:96], compare.ALPHABET)
            self.assertLessEqual(len(first), capacity)
            self.assertTrue(all(r["gain"] > 0 for r in report["trace"]))
            self.assertEqual(report["fit_total_selections"], sum(len(compare.scorer.shortest_encode(t, first)) for t in texts.values()))

    def test_cached_absent_programs_match_full_rescore(self):
        populations = [
            {"a": "red alpha\nred alpha\ntail a\n",
             "b": "blue beta\nblue beta\ntail b\n"},
            {"a": "same one\nsame two\nleft\n",
             "b": "same one\nsame two\nright\n", "c": "different\nlast\n"},
        ]
        for texts in populations:
            for capacity in (128, 256):
                chosen, trace = [], []
                remaining = set(compare.candidate_pool(texts))
                incumbent = sum(map(len, texts.values()))
                evaluations = 0
                while remaining and len(chosen) < capacity - len(compare.ALPHABET):
                    trials = []
                    for piece in sorted(remaining):
                        vocabulary = compare.ALPHABET + sorted(chosen + [piece])
                        count = sum(len(compare.scorer.shortest_encode(text, vocabulary))
                                    for text in texts.values())
                        trials.append((count, len(piece.encode()), piece))
                        evaluations += 1
                    count, _, piece = min(trials)
                    if count >= incumbent:
                        break
                    chosen.append(piece)
                    remaining.remove(piece)
                    trace.append({"step": len(chosen), "literal": piece,
                                  "before": incumbent, "after": count,
                                  "gain": incumbent - count})
                    incumbent = count
                with mock.patch.object(compare, "minimum_count", wraps=compare.minimum_count) as calls:
                    actual, report = compare.fit_dictionary(texts, capacity)
                self.assertEqual(actual, compare.ALPHABET + sorted(chosen))
                self.assertEqual(report["trace"], trace)
                self.assertEqual(report["evaluations"], evaluations)
                self.assertEqual(report["fit_total_selections"], incumbent)
                self.assertLess(calls.call_count, evaluations * len(texts))
                self.assertTrue(all(call.args[2] for call in calls.call_args_list))

    def test_cpu_expiry_is_failure_not_partial_success(self):
        with mock.patch.object(compare, "CPU_SECONDS_PER_FIT", -1):
            with self.assertRaisesRegex(RuntimeError, "arm failed"):
                compare.fit_dictionary({"a": "one\ntwo\n", "b": "one\nthree\n"}, 128)

    def test_malformed_cap_and_pool_limit_rejected(self):
        with self.assertRaises(ValueError):
            compare.fit_dictionary({"a": "alpha"}, 64)
        with mock.patch.object(compare, "MAX_POOL_ENTRIES", 1), self.assertRaises(ValueError):
            compare.candidate_pool({"a": "one\ntwo\n", "b": "three\nfour\n"})

    def test_measure_counts_full_helper_and_framing(self):
        texts = {"a": "helper\ncaller a\n", "b": "helper\ncaller b\n"}
        vocabulary, _ = compare.fit_dictionary(texts, 128)
        result, blobs = compare.measure(texts, vocabulary, 7)
        self.assertEqual(result["source_utf8_bytes"], sum(len(t.encode()) for t in texts.values()))
        self.assertEqual(result["dictionary_framing_bytes"], 8 + 4 * len(vocabulary))
        self.assertEqual(result["packet_framing_bytes"], 82)
        self.assertEqual(result["package_bytes"], len(blobs["dictionary"]) + sum(map(len, blobs["packets"].values())))
        self.assertEqual(result["single_character_bits"], 7 * sum(r["single_character_selections"] for r in result["per_problem"].values()))
        for pid, packet in blobs["packets"].items():
            self.assertEqual(compare.independent_decode(blobs["dictionary"], packet), texts[pid].encode())

    def test_independent_packet_decoder_malformed_controls(self):
        literals = ["a", "b", "ab"]
        dictionary = compare.scorer.dictionary_bytes(literals)
        packet = compare.codec.packet([2, 0, 1], 2, dictionary)
        self.assertEqual(compare.independent_decode(dictionary, packet), b"abab")
        mutated = []
        for offset, value in ((0, ord("X")), (4, 0), (5, packet[5] ^ 1), (-1, packet[-1] | 1)):
            candidate = bytearray(packet)
            candidate[offset] = value
            mutated.append(bytes(candidate))
        mutated += [packet[:-1], packet + b"\0", compare.codec.packet([3], 2, dictionary)]
        for bad in mutated:
            with self.subTest(packet=bad), self.assertRaises(ValueError):
                compare.independent_decode(dictionary, bad)
        for bad in (dictionary[:7], dictionary[:-1], dictionary + b"\0", b"NOPE" + dictionary[4:],
                    compare.scorer.dictionary_bytes(["a"])[:8] + b"\0\0\0\0"):
            with self.subTest(dictionary=bad), self.assertRaises(ValueError):
                compare.independent_decode(bad, packet)

    def test_reproducible_packets_across_hash_seeds(self):
        code = """import compare, json
texts={'a':'shared one\\nprivate a\\n','b':'shared one\\nprivate b\\n'}
v,_=compare.fit_dictionary(texts,128)
r,b=compare.measure(texts,v,7)
print(json.dumps({'vocab':v,'result':r},sort_keys=True))
"""
        import os
        outputs = []
        for seed in ("1", "9901"):
            output = subprocess.check_output([sys.executable, "-B", "-c", code], cwd=compare.HERE,
                                             env={**os.environ, "PYTHONHASHSEED": seed}, timeout=20)
            outputs.append(output)
        self.assertEqual(outputs[0], outputs[1])

    def receipt(self):
        identities = [{"language": lang, "problem_id": pid, "variant": variant,
                       "sha256": compare.sha(f"{lang}-{pid}-{variant}".encode())}
                      for lang in compare.LANGUAGES for pid in compare.PROBLEMS for variant in compare.VARIANTS]
        contract = {"cases_by_problem": {pid: 3 for pid in compare.PROBLEMS}, "batch_cases": 128,
                    "cases_sha256": "synthetic-test-case-identity", "code_sha256": {"test": "inert"}}
        receipt = {"schema": "gamma.readable-joint-blocks.qualification.v1", "status": "passed", "success": True,
                   "failures": [], "candidate_executions": 12, "protected_access": False,
                   "cases_sha256": contract["cases_sha256"], "code_sha256": contract["code_sha256"],
                   "rows": [{**r, "passed": True, "checks_total": 3, "checks_passed": 3,
                             "independent_oracle_checks_total": 2, "predecessor_compatibility_checks_total": 1}
                            for r in identities]}
        return identities, receipt, contract

    def test_qualification_requires_exact_complete_success(self):
        identities, receipt, contract = self.receipt()
        compare.require_qualification(receipt, identities, contract)
        for field, value in (("status", "blocked"), ("success", False), ("success", 1), ("schema", "other"),
                             ("candidate_executions", 1), ("failures", [{"case": "failed"}]),
                             ("cases_sha256", "stale"), ("code_sha256", {}), ("protected_access", True)):
            bad = copy.deepcopy(receipt)
            bad[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                compare.require_qualification(bad, identities, contract)
        for field, value in (("sha256", "stale"), ("passed", False), ("checks_total", 0),
                             ("checks_total", True), ("checks_passed", 2),
                             ("independent_oracle_checks_total", 1), ("predecessor_compatibility_checks_total", 0)):
            bad = copy.deepcopy(receipt)
            bad["rows"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                compare.require_qualification(bad, identities, contract)
        for rows in (receipt["rows"][:-1], receipt["rows"] + receipt["rows"][:1]):
            with self.assertRaises(ValueError):
                compare.require_qualification({**receipt, "rows": rows}, identities, contract)

    def test_one_case_pass_flag_cannot_replace_full_qualification(self):
        identities, receipt, contract = self.receipt()
        for row in receipt["rows"]:
            row["checks_total"] = row["checks_passed"] = 1
        with self.assertRaisesRegex(ValueError, "qualification row"):
            compare.require_qualification(receipt, identities, contract)

    def test_qualification_bundle_rejects_fake_contract(self):
        identities, receipt, _ = self.receipt()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw = b"{}"
            (root / "contract.json").write_bytes(raw)
            receipt["qualification_contract_sha256"] = compare.sha(raw)
            target = root / "qualification.json"
            target.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, "qualification cases"):
                compare.validate_qualification_bundle(target, identities)

    def test_qualification_bundle_replays_complete_synthetic_observations(self):
        # This is an inert evidence fixture, not execution/qualification of the
        # actual candidate programs. Only the comparator and bundle reader run.
        real = compare.load_module("qualification_test_helpers", compare.HERE / "qualify.py")
        identities, receipt, _ = self.receipt()
        examples = {"547": ([[1]], 1, [[1]]), "841": ([[]], True, [[]]), "1091": ([[0]], 1, [[1]])}
        cases = {pid: [{"args": [before], "expected": expected, "expectation_mode": "independent-oracle"} for _ in range(3)]
                 for pid, (before, expected, _) in examples.items()}
        qualifier = SimpleNamespace(SCHEMA=real.SCHEMA, SEED=1, build_cases=lambda: cases,
                                    provenance=lambda: identities, json_bytes=real.json_bytes, sandbox=real.sandbox,
                                    parse_records=real.parse_records, judge_record=real.judge_record)
        contract = {"schema": real.SCHEMA, "seed": 1, "sources": identities,
                    "cases_sha256": compare.sha(real.json_bytes(cases)),
                    "code_sha256": {name: compare.sha((compare.HERE / name).read_bytes())
                                    for name in ("variants.py", "qualify.py", "QUALIFICATION.md")},
                    "cases_by_problem": {pid: 3 for pid in compare.PROBLEMS},
                    "case_origin": "synthetic_and_public_samples_only", "max_total_wall_seconds": 180,
                    "batch_cases": 128, "sandbox": "existing_algsolve.judge.sandbox.run_unmodified",
                    "sandbox_sha256": compare.sha(Path(real.sandbox.__file__).read_bytes()),
                    "runtime_paths": {"python": "/usr/bin/python3", "javascript": "/usr/bin/node"},
                    "protected_access": False}
        raw = real.json_bytes(contract)
        receipt.update(qualification_contract_sha256=compare.sha(raw), cases_sha256=contract["cases_sha256"],
                       code_sha256=contract["code_sha256"])
        for row in receipt["rows"]:
            row.update(independent_oracle_checks_total=3, predecessor_compatibility_checks_total=0)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "contract.json").write_bytes(raw)
            target = root / "qualification.json"
            target.write_text(json.dumps(receipt))
            for row in receipt["rows"]:
                before, expected, after = examples[row["problem_id"]]
                records = [{"i": i, "result": expected, "result_type": "boolean" if type(expected) is bool else "number",
                            "args_before": [before], "args_after": [after], "identities_preserved": True} for i in range(3)]
                stem = root / f'{row["language"]}-{row["problem_id"]}-{row["variant"]}-0'
                stem.with_suffix(".stdout").write_bytes(b"".join(real.json_bytes(r) for r in records + [{"done": 3}]))
                stem.with_suffix(".stderr").write_bytes(b"")
            with mock.patch.object(compare, "load_module", return_value=qualifier):
                self.assertEqual(compare.validate_qualification_bundle(target, identities), receipt)
                # Source hashes and all pass flags still match, but the evidence
                # observation is wrong. The bundle must not qualify from flags.
                path = root / "javascript-547-original-0.stdout"
                rows = [json.loads(line) for line in path.read_bytes().splitlines()]
                rows[0]["result"] = 2
                path.write_bytes(b"".join(real.json_bytes(row) for row in rows))
                with self.assertRaisesRegex(ValueError, "observations"):
                    compare.validate_qualification_bundle(target, identities)

    def test_blocked_receipt_never_enters_fit_or_creates_results(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "contract.json").write_text(json.dumps({"source_identities": []}))
            receipt = root / "blocked.json"
            receipt.write_text(json.dumps({"status": "blocked", "success": False}))
            output = root / "result"
            with mock.patch.object(compare, "validate_freeze"), mock.patch.object(compare, "fit_dictionary") as fit:
                with self.assertRaisesRegex(ValueError, "qualification"):
                    compare.run(root, receipt, output)
                fit.assert_not_called()
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
