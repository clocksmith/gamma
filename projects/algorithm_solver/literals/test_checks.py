"""Host-only self-checks; no candidate code is imported or executed."""
import copy
import itertools
import json
import math
import unittest
import checks as c


class Checks(unittest.TestCase):
    def test_deterministic_unique_inventory(self):
        self.assertEqual(c.canonical(c._generate()), c.canonical(c.cases_by_problem))
        self.assertEqual(set(c.METHODS), set(c.cases_by_problem))
        for cases in c.cases_by_problem.values():
            self.assertEqual(len(cases), len({c.canonical(x["args"]) for x in cases}))
            self.assertTrue(cases)

    def test_safe_numbers_ascii_and_oracle_repeat(self):
        def visit(value):
            if type(value) is int:
                self.assertLessEqual(abs(value), 2**53 - 1)
            elif type(value) is float:
                self.assertTrue(math.isfinite(value))
            elif type(value) is str:
                self.assertTrue(value.isascii())
            elif type(value) is list:
                for x in value:
                    visit(x)
        for problem, cases in c.cases_by_problem.items():
            for case in cases:
                visit(case["args"])
                visit(case["expected"])
                before = copy.deepcopy(case["args"])
                self.assertEqual(c.oracle(problem, case["args"]), case["expected"])
                self.assertEqual(before, case["args"])

    def test_authored_examples(self):
        examples = [
            (136, [[-3, 0, -3]], 0), (169, [[9, 2, 9]], 9),
            (242, ["aab", "abb"], False), (242, ["ab", "ba"], True),
            (387, ["aabbcdd"], 4), (575, [[1, 1, 2, 2]], 2),
            (771, ["a", "AaAa"], 2), (961, [[8, 1, 2, 8]], 8),
            (1051, [[2, 10, 1]], 3), (1108, ["0.10.100.255"], "0[.]10[.]100[.]255"),
            (1119, ["oabcdeu"], "bcd"),
            (121, [[8, 2, 7, 1, 5]], 5), (551, ["LALL"], True),
            (551, ["LLLP"], False), (594, [[4, 4, 4]], 0),
            (594, [[3, 2, 3, 4, 3]], 4),
            (605, [[0, 0, 1, 0, 0], 2], True), (605, [[0, 0, 0], 3], False),
            (643, [[-4, -3, -2], 2], -2.5), (657, ["ULDR"], True),
            (657, ["URD"], False), (674, [[1, 8, 2, 3, 4]], 3),
            (704, [[-2, 0, 3], 3], 2), (704, [[-2, 0, 3], 1], -1),
            (709, ["@AZ[az`"], "@az[az`"), (724, [[0, 0, 0]], 0),
        ]
        for problem, args, expected in examples:
            self.assertEqual(c.oracle(problem, args), expected)

    def test_small_secondary_specifications(self):
        # Different formulations from the primary oracle.
        for problem, cases in c.cases_by_problem.items():
            for case in cases:
                args, expected = case["args"], case["expected"]
                if problem == 136:
                    self.assertEqual(2 * sum(set(args[0])) - sum(args[0]), expected)
                elif problem == 169:
                    winners = [x for x in set(args[0]) if args[0].count(x) * 2 > len(args[0])]
                    self.assertEqual(winners, [expected])
                elif problem == 242:
                    self.assertEqual(all(args[0].count(x) == args[1].count(x) for x in set("".join(args))), expected)
                elif problem == 575 and len(args[0]) <= 6:
                    self.assertEqual(min(len(set(args[0])), len(args[0]) // 2), expected)
                elif problem == 1051:
                    self.assertEqual(sum(a != b for a, b in zip(args[0], sorted(args[0]))), expected)

    def test_only_inputs_leave_host(self):
        for problem in c.METHODS:
            packet = c.input_packet(problem, 0, 1)
            self.assertNotIn('"expected"', c.canonical(packet))
            self.assertEqual(set(packet["calls"][0]), {"args", "kwargs", "capture_args"})
            packet["calls"][0]["args"].append("sentinel")
            self.assertNotEqual(packet["calls"][0]["args"], c.cases_by_problem[problem][0]["args"])

    def test_correct_records_and_effect_rejection(self):
        for problem in c.METHODS:
            case = c.cases_by_problem[problem][0]
            row = {"i": 0, "result": case["expected"], "args_before": copy.deepcopy(case["args"]),
                   "args_after": copy.deepcopy(case["args"])}
            self.assertEqual(c.check_records(problem, 0, [row, {"done": 1}])["passed"], 1)
            bad = copy.deepcopy(row)
            bad["args_after"] = []
            self.assertEqual(c.check_records(problem, 0, [bad, {"done": 1}])["passed"], 0)
            bad = copy.deepcopy(row)
            bad["result"] = {"invented": True}
            self.assertEqual(c.check_records(problem, 0, [bad, {"done": 1}])["passed"], 0)
        index = next(i for i, x in enumerate(c.cases_by_problem[1051]) if x["args"][0] != sorted(x["args"][0]))
        case = c.cases_by_problem[1051][index]
        row = {"result": case["expected"], "args_before": case["args"], "args_after": [sorted(case["args"][0])]}
        self.assertFalse(c.check_observation(1051, index, row)["passed"])

    def test_exact_types_and_protocol(self):
        self.assertFalse(c.exact(True, 1))
        self.assertFalse(c.exact(1.0, 1))
        case = c.cases_by_problem[136][0]
        row = {"i": 0, "result": case["expected"], "args_before": case["args"], "args_after": case["args"]}
        for end in [{"done": True}, {"done": 1.0}, {"done": 2}, {"done": 1, "extra": 0}]:
            with self.assertRaises(ValueError):
                c.check_records(136, 0, [row, end])
        for index in [True, 0.0, 1, -1]:
            with self.assertRaises(ValueError):
                c.check_records(136, 0, [{**row, "i": index}, {"done": 1}])
        for observation in [{**row, "error": "bad"}, {**row, "load_error": "bad"}]:
            self.assertFalse(c.check_observation(136, 0, observation)["passed"])

    def test_duplicate_json_and_slice_refusal(self):
        with self.assertRaises(ValueError):
            json.loads('{"i":0,"i":0}', object_pairs_hook=c._object)
        for problem, offset, limit in [(True, 0, 1), (136, True, 1), (136, 0, True),
                                      (136, -1, 1), (136, 0, 17), (136, 999999, 1)]:
            with self.assertRaises(ValueError):
                c.input_packet(problem, offset, limit)

    def test_added_domains(self):
        for problem in (121, 551, 594, 605, 643, 657, 674, 704, 709, 724):
            for case in c.cases_by_problem[problem]:
                args = case["args"]
                if problem == 121:
                    self.assertTrue(args[0] and all(type(v) is int and 0 <= v <= 10000 for v in args[0]))
                elif problem == 551:
                    self.assertTrue(args[0] and set(args[0]) <= set("ALP"))
                elif problem in (594, 674):
                    self.assertTrue(args[0] and all(type(v) is int and abs(v) <= 10**9 for v in args[0]))
                elif problem == 605:
                    bed, n = args
                    self.assertTrue(1 <= len(bed) <= 12 and set(bed) <= {0, 1} and 0 <= n <= len(bed))
                    self.assertFalse(any(a == b == 1 for a, b in zip(bed, bed[1:])))
                elif problem == 643:
                    self.assertTrue(args[0] and all(type(v) is int and abs(v) <= 10000 for v in args[0]))
                    self.assertTrue(1 <= args[1] <= len(args[0]))
                elif problem == 657:
                    self.assertTrue(args[0] and set(args[0]) <= set("UDLR"))
                elif problem == 704:
                    self.assertEqual(args[0], sorted(set(args[0])))
                    self.assertTrue(args[0] and all(abs(v) <= 9999 for v in args[0]) and abs(args[1]) <= 9999)
                elif problem == 709:
                    self.assertTrue(1 <= len(args[0]) <= 100 and all(32 <= ord(x) <= 126 for x in args[0]))
                elif problem == 724:
                    self.assertTrue(args[0] and all(abs(v) <= 1000 for v in args[0]))

    def test_additional_secondary_specs(self):
        for case in c.cases_by_problem[605]:
            bed, n = case["args"]
            # Complete final occupancy states, distinct from subset-of-free-cells oracle.
            if len(bed) <= 6:
                feasible = any(
                    all(a <= b for a, b in zip(bed, final))
                    and sum(final) - sum(bed) >= n
                    and not any(a == b == 1 for a, b in zip(final, final[1:]))
                    for final in itertools.product((0, 1), repeat=len(bed))
                )
                self.assertEqual(feasible, case["expected"])
        for case in c.cases_by_problem[594]:
            values = case["args"][0]
            if len(values) <= 8:
                lengths = [values.count(v) + values.count(v + 1) for v in set(values) if v + 1 in values]
                self.assertEqual(max(lengths, default=0), case["expected"])
        for case in c.cases_by_problem[643]:
            values, k = case["args"]
            from fractions import Fraction
            target = max(Fraction(sum(values[i:i + k]), k) for i in range(len(values) - k + 1))
            self.assertEqual(float(target), case["expected"])

    def test_numeric_average_and_pure_flowerbed(self):
        for i, case in enumerate(c.cases_by_problem[643]):
            value = case["expected"]
            if value == int(value):
                row = {"result": int(value), "args_before": case["args"], "args_after": case["args"]}
                self.assertTrue(c.check_observation(643, i, row)["passed"])
                for bad in (True, float("nan"), float("inf"), value + 0.000001, 10**1000):
                    self.assertFalse(c.check_observation(643, i, {**row, "result": bad})["passed"])
                break
        i = next(i for i, x in enumerate(c.cases_by_problem[605]) if x["args"] == [[0], 1])
        case = c.cases_by_problem[605][i]
        self.assertTrue(case["expected"])
        row = {"result": True, "args_before": case["args"], "args_after": [[1], 1]}
        self.assertFalse(c.check_observation(605, i, row)["passed"])

    def test_result_and_input_json_roundtrip(self):
        for problem, cases in c.cases_by_problem.items():
            for i, case in enumerate(cases):
                row = {"result": case["expected"], "args_before": case["args"], "args_after": case["args"]}
                parsed = json.loads(json.dumps(row, allow_nan=False))
                self.assertTrue(c.check_observation(problem, i, parsed)["passed"])


if __name__ == "__main__":
    unittest.main()
