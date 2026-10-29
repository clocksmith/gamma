"""Boundary references against the Q cohort oracle, gap-mutant models, and lane plumbing.

Never reads or runs candidate sources; the sandbox is never invoked.
"""
from __future__ import annotations
import copy
import importlib.util
from itertools import permutations
import random
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import boundary_cases as B  # noqa: E402
import protocol as P  # noqa: E402

_spec = importlib.util.spec_from_file_location('q_boundary_test_original_protocol', HERE.parent/'continuation-q-qualification-20261028-v1'/'protocol.py')
Q = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(Q)
ORACLE = B.Q_ORACLES.reference


def small_tree(rng, n, max_depth):
    left, right = B.random_shape(n, rng, max_depth, rng.random(), rng.random())
    return B.tree_packet([0]*n, left, right, rng if rng.random() < 0.5 else None)


class ReferenceAgreement(unittest.TestCase):
    def test_two_sided_ladders_match_cohort_oracle(self):
        rng = random.Random(1); checked = 0
        for _ in range(600):
            length = rng.randint(1, 4)
            universe = sorted({''.join(rng.choice('abc') for _ in range(length)) for _ in range(30)})
            if len(universe) < 2:
                continue
            words = rng.sample(universe, min(len(universe), rng.randint(1, 15)))
            begin = rng.choice(universe); end = rng.choice(words)
            if begin == end:
                continue
            args = [begin, end, words]
            self.assertEqual(B.ladders_two_sided(*args), ORACLE(126, args), args); checked += 1
        self.assertGreater(checked, 400)

    def test_grid_closed_form_matches_cohort_oracle_and_move_enumeration(self):
        rng = random.Random(2)
        for width, height, letters in ((3, 4, None), (4, 3, None), (2, 3, 'ab'), (2, 2, 'abc')):
            for _ in range(4):
                zs = [None] if letters is None else list(letters)
                cells = [(x, y, z) for x in range(width) for y in range(height) for z in zs]
                begin, end = rng.sample(cells, 2)
                args, paths = B.grid_case(rng, width, height, begin, end, letters, include_begin=rng.random() < 0.5)
                expected = ORACLE(126, args)
                self.assertEqual(B.ladders_two_sided(*args), expected)
                self.assertEqual(len(expected), paths)
        # Third method on a boundary-size grid: every ordering of unit moves, mapped to words.
        args, paths = B.grid_case(rng, 25, 20, (0, 0, 'a'), (3, 2, 'b'), 'ab')
        moves = sorted(set(permutations('xxxyyz')))
        enumerated = []
        for order in moves:
            x, y, z = 0, 0, 'a'; path = [B.grid_word(x, y, z)]
            for move in order:
                if move == 'x':
                    x += 1
                elif move == 'y':
                    y += 1
                else:
                    z = 'b'
                path.append(B.grid_word(x, y, z))
            enumerated.append(path)
        self.assertEqual(sorted(enumerated), B.ladders_two_sided(*args)); self.assertEqual(paths, 60)

    def test_chain_words_form_induced_path(self):
        words = [B.chain_word(k) for k in range(51)]
        self.assertEqual(words[:5], ['aa', 'ba', 'bb', 'cb', 'cc']); self.assertEqual(words[-1], 'zz')
        for i in range(51):
            for j in range(51):
                self.assertEqual(B._hamming_one(words[i], words[j]), abs(i-j) == 1)

    def test_linear_root_leaf_sum_matches_cohort_oracle(self):
        rng = random.Random(3)
        for _ in range(400):
            n = rng.randint(1, 40); packet = small_tree(rng, n, 10)
            packet['values'] = [rng.randrange(10) for _ in range(n)]
            if B.root_leaf_sum_linear(packet) > B.SUM_LIMIT:
                continue
            self.assertEqual(B.root_leaf_sum_linear(packet), ORACLE(129, [packet]))
        for _ in range(30):
            packet = small_tree(rng, rng.randint(200, 1000), 10)
            total = B.tune_digits(packet, rng.randrange(B.SUM_LIMIT+1), rng)
            self.assertLessEqual(total, B.SUM_LIMIT)
            self.assertEqual(total, ORACLE(129, [packet]))

    def test_forward_sentences_match_cohort_oracle(self):
        rng = random.Random(4)
        for _ in range(500):
            s = ''.join(rng.choice('ab') for _ in range(rng.randint(1, 13)))
            subs = sorted({s[i:j] for i in range(len(s)) for j in range(i+1, min(len(s), i+10)+1)})
            words = sorted(set(rng.sample(subs, max(1, len(subs)//rng.randint(1, 4)))+[w for w in ('ba', 'bbb', 'c') if rng.random() < 0.3]))
            expected = ORACLE(140, [s, words])
            self.assertEqual(B.sentences_forward_feasible(s, words), expected)
            self.assertEqual(B.sentence_count(s, words), len(expected))

    def test_morris_preorder_matches_cohort_oracle(self):
        rng = random.Random(5)
        for _ in range(400):
            n = rng.randint(1, 100); packet = small_tree(rng, n, 100)
            packet['values'] = [rng.randint(-100, 100) for _ in range(n)]
            self.assertEqual(B.preorder_morris(packet), ORACLE(144, [packet]))


def gap_rows():
    pop = P.population(); data, owners = P.cases_and_owners(pop)
    split = {pid: ([r for r in rows if r['case_identity']['origin'] != 'q-boundary'],
                   [r for r in rows if r['case_identity']['origin'] == 'q-boundary']) for pid, rows in data.items()}
    return pop, data, owners, split


class GapMutantModels(unittest.TestCase):
    """Host-side models of the reviewers' accepted wrong programs. Not candidate code."""
    @classmethod
    def setUpClass(cls):
        cls.pop, cls.data, cls.owners, cls.split = gap_rows()

    def test_129_left_none_means_leaf_passes_originals_fails_boundary(self):
        def mutant(packet):
            total = 0; stack = [(packet['root'], 0)]
            while stack:
                v, prefix = stack.pop(); prefix = prefix*10+packet['values'][v]
                if packet['left'][v] is None:
                    total += prefix; continue
                stack.extend((c, prefix) for c in (packet['left'][v], packet['right'][v]) if c is not None)
            return total
        old, new = self.split[129]
        self.assertTrue(all(mutant(r['args'][0]) == r['expected'] for r in old))
        self.assertGreater(sum(mutant(r['args'][0]) != r['expected'] for r in new), 40)

    def test_144_right_push_only_under_left_passes_originals_fails_boundary(self):
        def mutant(packet):
            if packet['root'] is None:
                return []
            out = []; stack = [packet['root']]
            while stack:
                v = stack.pop(); out.append(packet['values'][v])
                if packet['left'][v] is not None:
                    if packet['right'][v] is not None:
                        stack.append(packet['right'][v])
                    stack.append(packet['left'][v])
            return out
        old, new = self.split[144]
        self.assertTrue(all(mutant(r['args'][0]) == r['expected'] for r in old))
        self.assertGreater(sum(mutant(r['args'][0]) != r['expected'] for r in new), 40)

    def test_140_unpruned_dfs_work_jumps_on_boundary(self):
        old, new = self.split[140]
        before = max(B.unpruned_dfs_nodes(*r['args']) for r in old)
        after = sorted(B.unpruned_dfs_nodes(*r['args']) for r in new)
        self.assertLess(before, 1000)
        self.assertGreaterEqual(sum(n >= 500000 for n in after), 4)
        self.assertGreater(max(len(r['args'][1]) for r in new), 999)
        self.assertGreater(max(len(r['expected']) for r in new), 3900)
        self.assertLessEqual(max(sum(map(len, r['expected'])) for r in new), B.SENTENCE_OUTPUT_CHARS_MAX)

    def test_126_partial_path_bfs_prefixes_jump_on_boundary(self):
        old, new = self.split[126]
        before = max(B.ladder_shortest_prefixes(r['args']) for r in old if r['args'][1] in r['args'][2])
        after = max(B.ladder_shortest_prefixes(r['args']) for r in new)
        self.assertLess(before, 100); self.assertGreater(after, 10**7)
        reachable = [r for r in new if r['expected']]
        self.assertGreaterEqual(max(len(r['args'][2]) for r in reachable), 500)
        self.assertGreaterEqual(max(len(r['expected']) for r in reachable), 5544)
        self.assertLessEqual(max(sum(map(len, r['expected'])) for r in new), B.LADDER_OUTPUT_WORDS_MAX)


class LanePlumbing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pop, cls.data, cls.owners, cls.split = gap_rows()

    def test_q_settings_unchanged(self):
        for name in ('LANGUAGES', 'NATIVE', 'SOURCES', 'OBSERVER', 'OBSERVER_PIN', 'LIMITS', 'ARGV', 'MAX_INPUT_BYTES', 'PER_STREAM_OUTPUT_BYTES',
                     'DISPATCH_POLICY', 'BATCH_POLICY', 'PROJECTION_POLICY', 'REVIEW_FLAGS', 'NATIVE_FLAGS', 'REPAIR_FLAGS', 'QUERY'):
            self.assertEqual(getattr(P, name), getattr(Q, name), name)
        self.assertEqual(P.Q_IDS, Q.IDS)
        for pid in P.IDS:
            self.assertEqual(P.review_flags(pid), Q.review_flags(pid)); self.assertEqual(P.wanted_origin(pid), Q.wanted_origin(pid))

    def test_eight_programs_same_selection_and_exclusions(self):
        qpop = Q.population()
        self.assertEqual(P.program_count(self.pop), 8)
        self.assertEqual(self.pop['programs'], [r for r in qpop['programs'] if r['problem_id'] in P.IDS])
        self.assertEqual(self.pop['excluded_superseded_variants'], qpop['excluded_superseded_variants'])
        self.assertEqual(self.pop['problems'], [r for r in qpop['problems'] if r['id'] in P.IDS])

    def test_original_q_cases_kept_in_order_and_boundary_rows_distinct(self):
        qdata, _ = Q.cases_and_owners(Q.population())
        for pid, rows in self.data.items():
            inherited = qdata[pid]
            self.assertEqual([{k: v for k, v in r.items() if k != 'case_identity'} for r in rows[:len(inherited)]],
                             [{k: v for k, v in r.items() if k != 'case_identity'} for r in inherited])
            self.assertEqual(len({P.encoded(r['args']) for r in rows}), len(rows))
            self.assertGreater(len(self.split[pid][1]), 50)
            for row in rows:
                B.validate(pid, row['args'])

    def test_plans_fit_unchanged_envelope(self):
        for pid, rows in self.data.items():
            plan = P.batch_plan(pid, rows)
            self.assertEqual(plan['blocked_cases'], []); self.assertEqual(plan['admitted_distinct_cases'], len(rows))
            for entry in plan['batches']:
                self.assertLessEqual(entry['input_bytes'], P.MAX_INPUT_BYTES)
                self.assertLessEqual(max(entry['projected_stdout_bytes'].values()), P.PER_STREAM_OUTPUT_BYTES)

    def test_every_row_correct_record_passes_and_wrong_record_fails(self):
        for pid, rows in self.data.items():
            owner = self.owners[pid]
            for row in rows:
                for language in P.LANGUAGES:
                    record = P.projected_record(pid, language, row, 0)
                    self.assertEqual(owner.check_observation(pid, row['args'], record, language), (True, None), (pid, row['case_identity']))
                wrong = copy.deepcopy(P.projected_record(pid, 'python', row, 0))
                result = wrong['result']
                if pid in (126, 140):
                    wrong['result'] = result[:-1] if result else [['x']] if pid == 126 else ['x']
                elif pid == 129:
                    wrong['result'] = result+1
                else:
                    wrong['result'] = result[::-1] if len(set(result)) > 1 else result+[0]
                self.assertFalse(owner.check_observation(pid, row['args'], wrong, 'python')[0])
                duplicated = copy.deepcopy(P.projected_record(pid, 'javascript', row, 0))
                if pid in (126, 140) and result:
                    duplicated['result'] = result+result[:1]
                    self.assertFalse(owner.check_observation(pid, row['args'], duplicated, 'javascript')[0])

    def test_bridge_delegates_within_budget_and_recomputes_beyond(self):
        bridge = self.owners[126]
        self.assertTrue(bridge.within_existing(126, ['hit', 'cog', ['hot', 'dot', 'dog', 'lot', 'log', 'cog']]))
        large = next(r for r in self.split[126][1] if len(r['args'][2]) == 500 and r['expected'])
        self.assertFalse(bridge.within_existing(126, large['args']))
        self.assertEqual(bridge.expected(126, large['args']), B.ladders_two_sided(*large['args']))
        for pid in (126, 140):
            self.assertIs(self.owners[pid], self.owners[126])
            for row in self.data[pid]:
                self.assertEqual(self.owners[pid].expected(pid, row['args']), row['expected'])

    def test_review_binding_names_boundary_files(self):
        for program in self.pop['programs']:
            binding = P.review_binding(self.pop, program)
            self.assertEqual(binding['boundary_cases_sha256'], P.sha((HERE/'boundary_cases.py').read_bytes()))
            self.assertEqual(binding['boundary_checker_sha256'] is None, program['problem_id'] in (129, 144))

    def test_coverage_summary_reports_boundary_extents(self):
        summary = P.coverage_summary(self.data)
        self.assertEqual(summary['129']['max_prepared_expected_integer'], B.SUM_LIMIT)
        self.assertGreater(summary['144']['right_only_child_nodes'], 100)
        self.assertGreater(summary['126']['max_prepared_expected_path_count'], 5000)
        self.assertEqual(summary['140']['max_prepared_dictionary_words'], 1000)


if __name__ == '__main__':
    unittest.main()
