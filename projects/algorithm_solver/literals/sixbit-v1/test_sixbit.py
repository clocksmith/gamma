"""Focused checks on synthetic corpora: model exactness against brute force, certificate
signs, and the escape codec. No cohort search runs here."""
from itertools import combinations
import unittest

import model
import escape6
import escape6_decoder
import verify
from literals import dictionary_bytes

TEXTS = {'1': 'abab\nc', '2': 'abba\n', '3': 'bab\nab', '4': 'ca\nbb'}
SCALE = 1 << 20


def substrings(texts):
    return sorted({t[i:j] for t in texts.values() for i in range(len(t)) for j in range(i + 1, len(t) + 1)})


def brute_min_entries(texts, rule):
    ok = verify.eligible(rule, texts)
    pool = [s for s in substrings(texts) if ok(s)]
    def covers(vocab, t):
        reach = [True] + [False] * len(t)
        for i in range(len(t)):
            if reach[i]:
                for s in vocab:
                    if t.startswith(s, i):
                        reach[i + len(s)] = True
        return reach[-1]
    for k in range(1, len(pool) + 1):
        for vocab in combinations(pool, k):
            if all(covers(vocab, t) for t in texts.values()):
                return k
    return None


def certificate(graph, kind, **extra):
    res, potentials, mu = model.solve_lp(graph, kind, 60, **extra)
    return res.fun, {'scale': SCALE, 'mu': int(round(mu * SCALE)), 'potentials': model.program_potentials(graph, potentials, SCALE)}


class Exactness(unittest.TestCase):
    def test_min_entries_matches_brute_force_under_both_rules(self):
        for rule in ('W', 'U'):
            graph = model.Graph(TEXTS, rule)
            res = model.solve_milp(graph, 'A', 60)
            self.assertEqual(round(res.fun), brute_min_entries(TEXTS, rule), rule)
            shared, parses = model.solution(graph, res)
            used = {s for r in parses.values() for s, _ in r[2]}
            self.assertLessEqual(len(used), round(res.fun))
            self.assertTrue(all(''.join(s for s, _ in r[2]) == TEXTS[p] for p, r in parses.items()))

    def test_whole_programs_are_never_entries(self):
        graph = model.Graph({'1': 'xy', '2': 'xyxy'}, 'U')
        self.assertNotIn('xy', graph.strings)
        res = model.solve_milp(graph, 'A', 60)
        self.assertEqual(round(res.fun), 2)  # 'x' and 'y'

    def test_private_strings_are_one_entry_each(self):
        graph = model.Graph({'1': 'qqqzw', '2': 'qqq'}, 'U')
        res = model.solve_milp(graph, 'A', 60)
        self.assertEqual(round(res.fun), brute_min_entries({'1': 'qqqzw', '2': 'qqq'}, 'U'))


    def test_coverage_then_selections_under_a_budget(self):
        texts = {'1': 'abab', '2': 'abba', '3': 'xyz', '4': 'ba'}
        graph = model.Graph(texts, 'W')
        first = model.solve_milp(graph, 'B1', 60, budget=2)
        self.assertEqual(round(-first.fun), 3)  # 'a' and 'b' cover all but 'xyz'
        second = model.solve_milp(graph, 'B2', 60, budget=2, min_covered=3)
        shared, parses = model.solution(graph, second)
        self.assertEqual(sorted(p for p, r in parses.items() if r), ['1', '2', '4'])
        self.assertEqual(sum(r[0] for r in parses.values() if r), round(second.fun))
        self.assertEqual(round(second.fun), 10)  # 'ba' is a whole program, so only 'a' and 'b' cover three


class Certificates(unittest.TestCase):
    def test_lagrangian_bound_matches_lp_and_never_exceeds_the_integer_optimum(self):
        for rule in ('W', 'U'):
            graph = model.Graph(TEXTS, rule)
            lp, cert = certificate(graph, 'A')
            bound, scale = verify.lagrangian(TEXTS, rule, 'A', cert)
            self.assertAlmostEqual(bound / scale, lp, places=3)
            self.assertLessEqual(bound / scale, brute_min_entries(TEXTS, rule) + 1e-9)

    def test_budgeted_bounds_match_the_lp_when_the_budget_binds(self):
        graph = model.Graph(TEXTS, 'U')
        lp, cert = certificate(graph, 'B1', budget=2)
        self.assertGreater(cert['mu'], 0)
        bound, scale = verify.lagrangian(TEXTS, 'U', 'B1', cert, budget=2)
        self.assertAlmostEqual(bound / scale, len(TEXTS) + lp, places=3)
        graph = model.Graph(TEXTS, 'W', escapes=True)
        lp, cert = certificate(graph, 'C', budget=2)
        self.assertGreater(cert['mu'], 0)
        bound, scale = verify.lagrangian(TEXTS, 'W', 'C', cert, budget=2)
        self.assertAlmostEqual(bound / scale, lp, places=2)
        res = model.solve_milp(graph, 'C', 60, budget=2)
        self.assertLessEqual(bound / scale, res.fun + 1e-6)


class Escape(unittest.TestCase):
    def test_round_trip_and_press_accounting(self):
        entries = ['ab', '\n']
        dictionary = dictionary_bytes(entries)
        tokens = [('d', 0), ('e', 'Z'), ('d', 1), ('e', '@')]
        packet = escape6.encode(dictionary, entries, tokens)
        self.assertEqual(escape6_decoder.decode(dictionary, packet), 'abZ\n@')
        self.assertEqual(escape6.presses(tokens), 7 * 2 + 15 * 2)
        with self.assertRaises(ValueError):
            escape6_decoder.decode(dictionary, packet[:-1])
        with self.assertRaises(ValueError):
            escape6.encode(dictionary, entries, [('e', '\t')])

    def test_budgeted_codec_model_uses_escapes_when_entries_run_out(self):
        texts = {'1': 'aaaaXb', '2': 'aaYbb'}
        graph = model.Graph(texts, 'W', escapes=True)
        res = model.solve_milp(graph, 'C', 60, budget=1)
        shared, parses = model.solution(graph, res, press=(7, 15))
        used = {s for r in parses.values() for s, k in r[2] if k != 'e'}
        self.assertLessEqual(len(used), 1)
        self.assertEqual(sum(r[0] for r in parses.values()), round(res.fun))
        self.assertTrue(all(''.join(s for s, _ in r[2]) == texts[p] for p, r in parses.items()))


if __name__ == '__main__':
    unittest.main()
