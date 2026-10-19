import copy
import time
import unittest

from algsolve.synth.typed_literal_repair import literal_search, run_literal_route
from algsolve.synth.typed_prediction_codec import BITS, OPS, PredictionCodec
from algsolve.synth import typed_program
from test_typed_comparison import pair, graph, capture, CONFIG


class LiteralRepairTests(unittest.TestCase):
    def setUp(self):
        self.encoding = PredictionCodec.fit([pair(), pair(7)])
        self.codes, _ = capture(self.encoding, graph(0))
        self.slot = next(i for i,v in enumerate(self.codes['op']) if OPS[v]=='int')
        self.logits = [[10. if bit else -10. for bit in row] for row in self.codes['bits']]
        self.logits[self.slot][1] = -.1
        self.logits[self.slot][2] = -.2
        self.config = dict(pool_size=2,max_edits=2,max_executions=4,wall_seconds=.25)

    def search(self, evaluate, **kwargs):
        return literal_search(self.encoding,self.codes,self.logits,['x'],self.config,
                              evaluate,deadline=time.perf_counter()+1,**kwargs)

    def test_ordered_single_and_two_bit_choices_preserve_nonliteral_codes(self):
        before = copy.deepcopy(self.codes); seen=[]
        def evaluate(program, seconds):
            value=typed_program.execute(program,{'x':0});seen.append(value)
            return dict(passed=value==3,reason=None if value==3 else 'wrong_answer')
        result=self.search(evaluate)
        self.assertEqual(seen,[1,2,3])
        self.assertEqual(result['reason'],'literal_public_passed')
        self.assertEqual(len(result['edits']),2)
        self.assertEqual(self.codes,before)
        for k in before:
            if k!='bits':self.assertEqual(result['final_codes'][k],before[k])

    def test_rejects_nonfinite_or_mismatched_capture_before_execution(self):
        for corrupt in ['nan','mismatch']:
            with self.subTest(corrupt=corrupt):
                old=self.logits[self.slot][1]
                self.logits[self.slot][1]=float('nan') if corrupt=='nan' else 1.
                result=self.search(lambda *a:self.fail('must not execute'))
                self.assertEqual(result['reason'],'invalid_literal_capture')
                self.logits[self.slot][1]=old

    def test_execution_budget_and_infrastructure_stop(self):
        self.config['max_executions']=1
        r=self.search(lambda *a:dict(passed=False,reason='wrong_answer'))
        self.assertEqual(r['executions'],1)
        self.assertEqual(r['reason'],'literal_execution_budget')
        self.config['max_executions']=4
        r=self.search(lambda *a:dict(passed=False,reason='sandbox_error'))
        self.assertEqual(r['executions'],1);self.assertTrue(r['infrastructure_failure'])

    def test_expired_budget_does_not_execute(self):
        r=literal_search(self.encoding,self.codes,self.logits,['x'],self.config,
                         lambda *a:self.fail('expired'),deadline=time.perf_counter()-1)
        self.assertEqual(r['executions'],0);self.assertEqual(r['reason'],'literal_budget')

    def test_accepted_control_is_never_searched(self):
        control=dict(decision='answered',timing={'total_seconds':.1},source='kept')
        result=run_literal_route(control,None,None,None,None,self.config,2)
        self.assertEqual(result['decision'],'answered');self.assertEqual(result['source'],'kept')
        self.assertIsNone(result['literal_repair']);self.assertNotIn('literal_repair',control)


if __name__=='__main__':unittest.main()
