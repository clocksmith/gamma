"""Comparison accounting/resume tests; synthetic development fixtures only."""
import copy
from pathlib import Path
import tempfile
import unittest
import numpy as np

from algsolve.compare_requirements import SharedInputs, summarize, check_control, score_pair_receipts
from algsolve.rebuild_recognition import bound_receipt


def arm(correct=False,accepted=False,wrong=False,unqualified=False,infra=False):
    return {'correct':correct,'accepted':accepted,'wrong':wrong,'unqualified':unqualified,
            'infrastructure_error':infra,'charged_route_seconds':1.,'within_route_budget':True}


class PairedDevelopment(unittest.TestCase):
    def test_shared_retrieval_identity_order_and_copy(self):
        cs=[{'key':'renamed','score':.75}];v=np.ones(3)
        cache=SharedInputs(object(),'text',v,cs)
        encoded=cache.encode(['text'],query=True);encoded[:]=0
        self.assertTrue(np.array_equal(v,np.ones(3)))
        first=cache.scored_candidates('text',v);first[0]['score']=5
        self.assertEqual(cache.scored_candidates('text',v),cs)
        for text,vector in [('other',v),('text',np.zeros(3))]:
            with self.assertRaises(ValueError):cache.scored_candidates(text,vector)
        with self.assertRaises(ValueError):cache.encode(['text'],query=False)

    def test_gain_and_harm_report_correctness_not_validity(self):
        rows=[{'id':'original-success','kind':'informal','control':arm(True,True),'candidate':arm(True,True)},
              {'id':'new-answer','kind':'informal','control':arm(),'candidate':arm(True,True)},
              {'id':'pre-gate','kind':'ambiguous','control':arm(),'candidate':arm()}]
        report=summarize(rows)
        self.assertEqual(report['useful_changes'],['new-answer'])
        self.assertTrue(report['retain_as_development_candidate']);self.assertFalse(report['release_qualified'])
        self.assertEqual(report['no_example_pre_retrieval_controls']['candidate']['requests'],1)
        for field in ('correct','wrong','unqualified','infrastructure_error','within_route_budget'):
            changed=copy.deepcopy(rows)
            if field=='correct':changed[0]['candidate'][field]=False
            elif field=='within_route_budget':changed[1]['candidate'][field]=False
            else:changed[1]['candidate'][field]=True
            with self.subTest(field=field):self.assertFalse(summarize(changed)['retain_as_development_candidate'])

    def test_receipt_resumption_does_not_repeat_inference_or_judge(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'arm.json';calls=[]
            make=lambda:(calls.append(1) or {'decision':'abstain','reason':'sandbox_error'})
            self.assertEqual(bound_receipt(path,{'candidate':'A'},make),bound_receipt(path,{'candidate':'A'},make))
            self.assertEqual(len(calls),1)
            with self.assertRaises(ValueError):bound_receipt(path,{'candidate':'B'},make)

    def test_interruption_between_scoring_arms_resumes_only_missing_arm(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);calls=[]
            def interrupted(arm):
                calls.append(arm)
                if arm=='candidate':raise RuntimeError('interrupted development fixture')
                return {'correct':True}
            with self.assertRaises(RuntimeError):score_pair_receipts(root,0,{'candidate':'A'},interrupted)
            resumed=score_pair_receipts(root,0,{'candidate':'A'},lambda arm:(calls.append(arm) or {'correct':True}))
            self.assertEqual(calls,['control','candidate','candidate'])
            self.assertTrue(resumed['control']['correct'])

    def test_control_guard_rejects_changed_contents_or_mtime(self):
        from unittest.mock import patch
        original={'x':{'sha256':'a','mtime_ns':1}}
        for current in ({'x':{'sha256':'b','mtime_ns':1}}, {'x':{'sha256':'a','mtime_ns':2}}):
            with patch('algsolve.compare_requirements.snapshot',return_value=current):
                with self.assertRaises(ValueError):check_control(original)

if __name__=='__main__':unittest.main()
