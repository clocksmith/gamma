import copy
import time
import unittest
from unittest.mock import patch

from algsolve.synth import typed_codec, typed_program as ir, typed_recipes as r
from algsolve.synth.typed_prediction_codec import OPS, PredictionCodec
from algsolve.synth.typed_semantic_repair import semantic_search, run_semantic_route
from test_typed_comparison import capture


class SemanticRepairTests(unittest.TestCase):
    def setUp(self):
        program = r.program({'x': ir.INTS}, [r.invoke('stable_unique', 'y', r.ref('x'))], r.ref('y'), ir.INTS)
        self.encoding = PredictionCodec.fit([dict(learning_split='development_fit', target=typed_codec.encode(program,'fixture'))])
        self.codes,self.logits = capture(self.encoding,program)
        self.logits['bits'] = [[10. if b else -10. for b in row] for row in self.codes['bits']]
        self.slot = next(i for i,v in enumerate(self.codes['op']) if OPS[v]=='recipe:stable_unique')
        self.logits['op'][self.slot][OPS.index('recipe:heap_sort')]=9.
        self.config = dict(pool_size=8,max_edits=2,max_executions=4,wall_seconds=.25)

    def search(self,evaluate,**kw):
        return semantic_search(self.encoding,self.codes,self.codes,self.logits,['x'],self.config,
                               evaluate,deadline=kw.get('deadline',time.perf_counter()+1))

    def test_model_ranked_recipe_repairs_wrong_valid_graph_without_other_edits(self):
        before=copy.deepcopy(self.codes);seen=[]
        def evaluate(program,seconds):
            value=ir.execute(program,{'x':[3,1,3]},recipes=r.catalog());seen.append(value)
            return dict(passed=value==[1,3,3],reason=None)
        result=self.search(evaluate)
        self.assertEqual(seen,[[1,3,3]])
        self.assertEqual(result['reason'],'recipe_public_passed')
        self.assertEqual(result['executions'],1)
        self.assertEqual(self.codes,before)
        for key in before:
            if key!='op':self.assertEqual(result['final_codes'][key],before[key])

    def test_wrong_recipe_ports_rejected_before_public_execution(self):
        self.logits['op'][self.slot][OPS.index('recipe:forest')]=9.5
        result=self.search(lambda *a:dict(passed=True,reason=None))
        self.assertTrue(result['attempts'][0]['validation_failure'])
        self.assertIsNone(result['attempts'][0]['public'])
        self.assertEqual(result['executions'],1)

    def test_rejects_capture_mismatch_and_nonfinite_before_execution(self):
        for value in [11.,float('nan')]:
            with self.subTest(value=value):
                self.logits['op'][self.slot][OPS.index('recipe:heap_sort')]=value
                result=self.search(lambda *a:self.fail('must not execute'))
                self.assertEqual(result['reason'],'invalid_semantic_capture')

    def test_recipe_and_literal_share_execution_and_wall_budget(self):
        with patch('algsolve.synth.typed_semantic_repair.literal_search') as fallback:
            fallback.return_value=dict(pool=[],attempts=[],edits=[],final_codes=None,graph=None,
                                       executions=0,reason='none',infrastructure_failure=False,seconds=0.)
            result=self.search(lambda *a:dict(passed=False,reason='wrong_answer'))
            self.assertEqual(result['executions'],1)
            self.assertEqual(fallback.call_args.args[4]['max_executions'],3)
            self.assertLessEqual(fallback.call_args.kwargs['deadline'],time.perf_counter()+.25)
        self.config['max_executions']=1
        with patch('algsolve.synth.typed_semantic_repair.literal_search') as fallback:
            result=self.search(lambda *a:dict(passed=False,reason='wrong_answer'))
            self.assertEqual(result['executions'],1);fallback.assert_not_called()

    def test_infrastructure_failure_and_expired_budget_stop(self):
        with patch('algsolve.synth.typed_semantic_repair.literal_search') as fallback:
            result=self.search(lambda *a:dict(passed=False,reason='sandbox_error'))
            self.assertTrue(result['infrastructure_failure']);fallback.assert_not_called()
        result=self.search(lambda *a:self.fail('expired'),deadline=time.perf_counter()-1)
        self.assertEqual(result['executions'],0)

    def test_preserves_accepted_control_and_charges_overhead(self):
        control=dict(decision='answered',timing={'total_seconds':.1},source='kept')
        result=run_semantic_route(control,None,None,None,None,self.config,2.)
        self.assertEqual(result['source'],'kept');self.assertEqual(result['decision'],'answered')
        self.assertIsNone(result['semantic_repair'])
        self.assertGreater(result['timing']['total_seconds'],.1)
        result=run_semantic_route(control,None,None,None,None,self.config,0.)
        self.assertEqual(result['decision'],'abstain')

if __name__=='__main__':unittest.main()
