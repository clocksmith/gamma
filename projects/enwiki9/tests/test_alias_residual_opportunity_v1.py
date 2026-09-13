import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from alias_residual_opportunity_v1 import census


class CausalityTests(unittest.TestCase):
    def run_census(self, raw):
        return census(raw, raw, lambda position: position)

    def test_cross_form_transfer_and_disrupted_edge(self):
        raw = (b'<page>Alpha Beta (AB)\nGamma Delta (GD)\n'
               b'Alpha Beta sameword tail\nGamma Delta different tail\nAB sameword tail\n')
        result = self.run_census(raw)
        self.assertEqual(len(result['opportunities']['D']), 1)
        self.assertTrue(result['opportunities']['D'][0]['exact_window_match'])
        self.assertEqual(len(result['opportunities']['S']), 1)
        self.assertFalse(result['opportunities']['S'][0]['exact_window_match'])
        for rows in result['opportunities'].values():
            for row in rows:
                self.assertLessEqual(row['donor_wrt'] + 8, row['target_wrt'])

    def test_future_definition_supplies_no_history(self):
        raw = b'Alpha Beta sameword tail\nAB sameword tail\nAlpha Beta (AB)\n'
        self.assertFalse(self.run_census(raw)['opportunities']['D'])

    def test_page_reset_forgets_alias_and_donors(self):
        raw = b'<page>Alpha Beta (AB)\nAlpha Beta sameword tail\n<page>AB sameword tail\n'
        self.assertFalse(self.run_census(raw)['opportunities']['D'])

    def test_conflicting_definition_disables_alias(self):
        raw = b'Alpha Beta (AB)\nAlpha Beta sameword tail\nAnother Branch (AB)\nAB sameword tail\n'
        result = self.run_census(raw)
        self.assertEqual(result['counts']['ambiguous_aliases'], 1)
        self.assertFalse(result['opportunities']['D'])

    def test_incomplete_donor_window_is_unavailable(self):
        raw = b'Alpha Beta (AB)\nAlpha Beta AB sameword tail\n'
        self.assertFalse(self.run_census(raw)['opportunities']['D'])


if __name__ == '__main__':
    unittest.main()
