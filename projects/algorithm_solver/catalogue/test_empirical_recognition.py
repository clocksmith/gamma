import unittest
from .empirical_recognition import decide, rank, score_decisions, select_policy

class Service:
    def __init__(self): self.requests = []
    def request(self, ident, **kwargs):
        self.requests.append((ident, kwargs))
        if ident != 'leetcode:1': return {'status': 'abstain'}
        return {'status': 'matched', 'consumer_selection': {'status': 'selected', 'implementation': {'contract_sha256': 'c'}}}

class EmpiricalTests(unittest.TestCase):
    def setUp(self): self.service=Service(); self.policy={'id':'x','min_cosine':.5,'min_margin':.03}
    def test_accept_scope_and_no_source(self):
        d=decide([('leetcode:1',.8),('leetcode:2',.6)],self.policy,self.service)
        self.assertEqual(d['status'],'accepted'); self.assertFalse(d['semantic_proof'])
        self.assertTrue(all(not kw['include_source'] for _,kw in self.service.requests))
    def test_unqualified_competitor_not_filtered(self):
        self.assertEqual(decide(rank([.6,.8],['leetcode:1','leetcode:2']),self.policy,self.service)['status'],'abstain')
    def test_tie_abstains_at_zero_margin(self):
        self.policy['min_margin']=0
        self.assertEqual(decide([('leetcode:1',.8),('leetcode:2',.8)],self.policy,self.service)['status'],'abstain')
    def test_truncation_no_service_access(self):
        self.assertEqual(decide([],self.policy,self.service,truncated=True)['status'],'abstain');self.assertFalse(self.service.requests)
    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):rank([float('nan'),.2],['a','b'])
    def test_evaluator_counts_controls(self):
        q=[{'kind':'positive','expected_id':'leetcode:1'},{'kind':'ambiguous'}]
        d=[{'status':'accepted','problem_id':'leetcode:1'},{'status':'accepted','problem_id':'leetcode:1'}]
        m=score_decisions(q,d);self.assertEqual(m['correct_accepts'],1);self.assertEqual(m['control_accepts'],1)
        self.assertIsNone(select_policy([{'policy':self.policy,'metrics':m}]))
    def test_selection_stricter_tie(self):
        m={'correct_accepts':3,'wrong_positive_accepts':0,'control_accepts':0}
        p2=dict(self.policy,id='y',min_cosine=.8)
        self.assertEqual(select_policy([{'policy':self.policy,'metrics':m},{'policy':p2,'metrics':m}]),p2)

if __name__ == '__main__':unittest.main()
