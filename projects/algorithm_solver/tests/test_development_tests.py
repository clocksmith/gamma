import unittest
from unittest.mock import patch

from algsolve.synth import development_tests as tests, mine


class DevelopmentTestIntegrity(unittest.TestCase):
    def test_missing_number_rejects_out_of_domain_source_case(self):
        with self.assertRaisesRegex(ValueError,'outside'):
            tests.missing_oracle([list(range(10000,9899,-1))])
        with self.assertRaisesRegex(ValueError,'distinct'):
            tests.missing_oracle([[0,0]])
        self.assertEqual(tests.missing_oracle([[3,0,1]]),2)

    def test_redundant_connection_enforces_one_cycle_and_last_valid_edge(self):
        with self.assertRaises(ValueError):
            tests.redundant_oracle([[[1,2],[2,3],[3,4],[1,4],[4,5],[5,1]]])
        # Six edges but only five vertices connected: not a valid six-vertex
        # tree plus one edge, even after normalizing endpoint orientation.
        with self.assertRaises(ValueError):
            tests.redundant_oracle([[[1,2],[2,3],[3,4],[1,4],[4,5],[1,5]]])
        self.assertEqual(tests.redundant_oracle([[[1,2],[1,3],[2,3]]]),[2,3])
        self.assertEqual(tests.redundant_oracle([[[2,3],[1,3],[1,2]]]),[1,2])

    def test_replacement_is_reproducible_and_does_not_mutate_originals(self):
        original=[{'args':[[0,0]],'expected':1,'compare':'return'}]
        original_hash=mine.digest(original)
        with patch.dict(tests.SOURCE_HASHES,{'lcd:268':original_hash}):
            replacement, receipt=tests.select('lcd:268',original)
        self.assertEqual(mine.digest(original),original_hash)
        self.assertEqual(replacement,tests.generated('lcd:268'))
        self.assertEqual(receipt['original_count'],1)
        self.assertEqual(len(receipt['rejected_original_cases']),1)
        self.assertNotEqual(receipt['sha256'],original_hash)

    def test_changed_original_or_missing_defect_cannot_silently_use_repair(self):
        valid=[{'args':[[0]],'expected':1}]
        with self.assertRaisesRegex(ValueError,'changed'): tests.select('lcd:268',valid)
        with patch.dict(tests.SOURCE_HASHES,{'lcd:268':mine.digest(valid)}):
            with self.assertRaisesRegex(ValueError,'requires reproduced'): tests.select('lcd:268',valid)
        data,receipt=tests.select('unrelated',valid)
        self.assertIs(data,valid)
        self.assertEqual(receipt['kind'],'imported_independent_tests')

    def test_generated_graph_cases_have_unique_cycle_and_valid_removal(self):
        for case in tests.generated('lcd:684'):
            edges=case['args'][0]
            self.assertEqual(len({tuple(e) for e in edges}),len(edges))
            remaining=list(edges); remaining.remove(case['expected'])
            self.assertEqual(len(remaining),len(edges)-1)
            self.assertTrue(tests.connected(len(edges),remaining))


if __name__=='__main__': unittest.main()
