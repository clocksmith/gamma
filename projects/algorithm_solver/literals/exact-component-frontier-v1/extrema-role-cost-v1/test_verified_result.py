import json
from pathlib import Path
import unittest

class VerifiedTests(unittest.TestCase):
    def test_all_sixteen_not_only_chosen_paths(self):
        r=json.loads(Path(__file__).with_name('ALL-ADDITIONS-VERIFIED-v1.json').read_text());v=r['verification'];rows=v['all_additions']
        self.assertTrue(v['verified']);self.assertEqual(v['exact_additions_checked'],16)
        self.assertEqual(len({(x['id'],x['arm'])for x in rows}),16)
        self.assertEqual({x['id']for x in rows},{'123','55','1014','1121','1375','1725','1732','2873'})
        self.assertTrue(all(x['reachable'] and x['byte_codepoint_dp_equal'] and x['packet_decoded_exactly']for x in rows))
        self.assertTrue(all(x['packet_bytes']==41+x['selections']for x in rows))
        self.assertTrue(v['reproduced_four_arm_metrics_and_storage'])
        c=r['cleanup'];self.assertEqual(c['exit_code'],0);self.assertFalse(c['wall_timeout']);self.assertTrue(c['no_executing_owned_processes_observed'])
        self.assertEqual(c['remaining_live_owned'],[]);self.assertEqual(c['inspection_unreadable_pids'],[])

if __name__=='__main__':unittest.main()
