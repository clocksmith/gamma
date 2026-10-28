"""Source-free reference controls. Never import or execute candidate files."""
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('continuation_a_oracles', Path(__file__).with_name('oracles.py'))
O = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(O)
EXAMPLES = {
    3623: [([[[1,0],[2,0],[3,0],[2,2],[3,2]]],3), ([[[0,0],[1,0],[0,1],[2,1]]],1)],
    3625: [([[[-3,2],[3,0],[2,3],[3,2],[2,-3]]],2), ([[[0,0],[1,0],[0,1],[2,1]]],1)],
    3627: [([[2,1,3,2,1,3]],5), ([[1,1,10,10,10,10]],20)],
    3628: [(['LMCT'],2), (['LCCT'],4), (['L'],0)],
    3629: [([[1,2,4,6]],2), ([[2,3,4,7,9]],2), ([[4,6,5,8]],3)],
    3634: [([[2,1,5],2],1), ([[1,6,2,9],3],2), ([[4,6],2],0)],
    3635: [([[2,8],[4,1],[6],[3]],9), ([[5],[3],[1],[10]],14)],
    3638: [([[2,5,1,4,3]],2), ([[4,4]],0)],
    3644: [([[0,3,2,1]],1), ([[0,1,3,2]],2), ([[3,2,1,0]],0)],
    3645: [([[3,5,8],[2,1,3]],16), ([[4,2,6],[1,1,1]],6), ([[4,1,5,2],[3,3,2,3]],12)],
}


class ReferenceControls(unittest.TestCase):
    def test_official_numeric_examples(self):
        for pid, examples in EXAMPLES.items():
            for args, want in examples:
                with self.subTest(pid=pid, args=args):
                    self.assertEqual(O.expected(pid, args), want)

    def test_degenerate_quadrilaterals_not_trapezoids(self):
        for pid in (3623, 3625):
            self.assertEqual(O.expected(pid, [[[0,0],[1,0],[2,0],[3,0]]]), 0)
            self.assertEqual(O.expected(pid, [[[0,0],[1,1],[2,2],[3,3]]]), 0)
        self.assertEqual(O.expected(3625, [[[0,0],[1,0],[1,1],[0,1]]]), 1)

    def test_prime_teleports_are_directed(self):
        self.assertEqual(O.expected(3629, [[6,1,1,2]]), 3)
        self.assertEqual(O.expected(3629, [[2,1,1,6]]), 1)
        self.assertEqual(O.expected(3629, [[1]]), 0)

    def test_skipped_parcels_and_strict_balance(self):
        self.assertEqual(O.expected(3638, [[9,1,9,1,9,1]]), 3)
        self.assertEqual(O.expected(3638, [[1,2,3,4]]), 0)
        self.assertEqual(O.expected(3638, [[4,4,3]]), 1)

    def test_activation_permanent_death_and_carrying_active_items(self):
        self.assertEqual(O.expected(3645, [[10,7,8],[1,1,1]]), 10)
        self.assertEqual(O.expected(3645, [[5,8,9,10],[2,3,3,3]]), 32)

    def test_permutation_graph_sorted_and_minimum_size(self):
        self.assertEqual(O.expected(3644, [[0]]), 0)
        self.assertEqual(O.expected(3644, [[1,0]]), 0)
        self.assertEqual(O.expected(3644, [[0,1,2,3]]), 0)

    def test_domain_boolean_float_shapes_and_duplicates(self):
        bad = [(True, [[1]]), (3623, [[[0,0]]*4]), (3627, [[1,2]]),
               (3628, ['lct']), (3629, [[True]]), (3634, [[1],True]),
               (3635, [[1],[2,3],[1],[1]]), (3638, [[1]]),
               (3644, [[0,0]]), (3645, [[1,2],[1,3]])]
        for pid, args in bad:
            with self.subTest(pid=pid), self.assertRaises(ValueError):
                O.validate(pid,args)

    def test_reference_work_bounds_do_not_reduce_domains(self):
        pairs = [(3627, [[1]*15]), (3628,['L'*13]), (3629,[[1]*31]),
                 (3634,[[1]*17,1]), (3638,[[1]*19]), (3644,[list(range(11))]),
                 (3645,[[1]*11,[1]*11])]
        for pid,args in pairs:
            O.validate(pid,args)
            with self.assertRaises(ValueError):
                O.expected(pid,args)

    def test_full_domain_boundaries_validate_without_candidate_runs(self):
        cases = [(3623,[[[i,10**8] for i in range(100000)]]),
                 (3625,[[[i,1000] for i in range(500)]]),
                 (3627,[[10**9]*499998]), (3628,['Z'*100000]),
                 (3629,[[10**6]*100000]), (3634,[[10**9]*100000,100000]),
                 (3635,[[100000]*50000 for _ in range(4)]),
                 (3638,[[10**9]*100000]), (3644,[list(range(100000))]),
                 (3645,[[100000]*100000,[100000]*100000])]
        for pid,args in cases:
            O.validate(pid,args)

    def test_seeded_bounded_cases_are_deterministic_and_inputs_unchanged(self):
        import copy
        first=O.synthetic_cases();self.assertEqual(first,O.synthetic_cases())
        for pid,args in first:
            before=copy.deepcopy(args);result=O.expected(pid,args)
            self.assertIs(type(result),int);self.assertGreaterEqual(result,0)
            self.assertEqual(args,before)


if __name__ == '__main__':
    unittest.main()
