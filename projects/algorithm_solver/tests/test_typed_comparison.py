import copy
import json
from pathlib import Path
import time
import unittest

from algsolve.judge.judge import Verdict
from algsolve.records import Problem
from algsolve.synth import typed_codec, typed_program
from algsolve.synth.typed_prediction_codec import PredictionCodec, OPS, INPUTS
from algsolve.synth.typed_correction import correct
from algsolve.synth.typed_comparison import (nearest_graph, run_route, score_fixed,
                                           correction_outcome, summarize)

CONFIG = json.loads((Path(__file__).parents[1]/'contracts/typed_composer_development_v1.json').read_text())


def graph(value=None):
    return {'schema':typed_program.SCHEMA, 'parameters':['x'], 'inputs':{'x':'int'},
            'body':[], 'return':{'ref':'x'} if value is None else {'literal':value}, 'output_type':'int'}


def pair(value=None, uid='fixture'):
    target = typed_codec.encode(graph(value),'fixture')
    return {'uid':uid, 'learning_split':'development_fit', 'graph_sha256':typed_codec.digest(target),
            'target':target, 'input':{'params':[['x','int']],
            'starter_code':'class Solution:\n    def solve(self, x: int) -> int:\n        pass\n'}}


def capture(encoding, program):
    raw = encoding.encode(program)
    for key in raw:
        raw[key] = [[max(0,x) for x in row] for row in raw[key]] if key=='bits' else [max(0,x) for x in raw[key]]
    dimensions = {'op':len(OPS),'first':encoding.slots+1,'next':encoding.slots+1,
                  'binding':INPUTS+encoding.slots,'types':len(encoding.types)}
    logits = {}
    for field,width in dimensions.items():
        logits[field] = [[-100.]*width for _ in raw[field]]
        for slot,value in enumerate(raw[field]):
            logits[field][slot][value] = 10.
    return raw,logits


def corrupt(raw, logits, field, slot, value):
    old = raw[field][slot]
    raw[field][slot] = value
    logits[field][slot][old] = 9.
    logits[field][slot][value] = 10.


class TypedComparisonTests(unittest.TestCase):
    def setUp(self):
        self.encoding = PredictionCodec.fit([pair(),pair(7)])
        self.config = {**CONFIG['correction'],'wall_seconds':2.}
        self.problem = Problem('fixture','fixture','0','fixture','fixture','return x','functional',
            params=[['x','int']],entry={'class':'Solution','method':'solve'},
            public_tests=[{'args':[3],'expected':3}])

    def test_valid_but_wrong_program_is_unchanged(self):
        raw,logits = capture(self.encoding,graph(7))
        original = copy.deepcopy(raw)
        result = correct(self.encoding,raw,logits,['x'],self.config)
        self.assertEqual(result['reason'],'already_valid')
        self.assertEqual(raw,original)
        self.assertEqual(result['final_codes'],original)
        self.assertEqual(result['attempts'],[])
        self.assertEqual(typed_program.execute(result['graph'],{'x':3}),7)

    def test_cyclic_edge_repair_retains_raw_and_reasons(self):
        raw,logits = capture(self.encoding,graph())
        corrupt(raw,logits,'first',0,1)
        original = copy.deepcopy(raw)
        result = correct(self.encoding,raw,logits,['x'],self.config)
        self.assertEqual(result['reason'],'schema_repaired')
        self.assertEqual(raw,original)
        self.assertIn('edge',result['raw_validation_failure'])
        self.assertEqual(result['edits'][0]['field'],'first')
        self.assertTrue(result['edits'][0]['reason'])
        self.assertEqual(typed_program.execute(result['graph'],{'x':3}),3)
        self.assertEqual(result['final_codes']['bits'],raw['bits'])

    def test_two_coordinate_repair_and_deterministic_attempt_order(self):
        raw,logits = capture(self.encoding,graph())
        corrupt(raw,logits,'first',0,1)
        ref = next(i for i,v in enumerate(raw['op']) if OPS[v]=='ref')
        corrupt(raw,logits,'binding',ref,INPUTS+self.encoding.slots-1)
        one = correct(self.encoding,raw,logits,['x'],self.config)
        two = correct(self.encoding,raw,logits,['x'],self.config)
        self.assertEqual(one['reason'],'schema_repaired')
        self.assertEqual(len(one['edits']),2)
        self.assertEqual(one['attempts'],two['attempts'])
        self.assertTrue(any(a['validation_failure'] for a in one['attempts']))

    def test_bounds_reject_without_substitution(self):
        raw,logits = capture(self.encoding,graph())
        corrupt(raw,logits,'first',0,1)
        result = correct(self.encoding,raw,logits,['x'],{**self.config,'max_candidates':0})
        self.assertIsNone(result['graph']); self.assertEqual(result['attempts'],[])
        result = correct(self.encoding,raw,logits,['x'],self.config,deadline=time.perf_counter()-1)
        self.assertIsNone(result['graph']); self.assertEqual(result['reason'],'correction_budget')

    def test_mismatched_and_nonfinite_scores_rejected(self):
        raw,logits = capture(self.encoding,graph())
        raw['first'][0] = 1
        result = correct(self.encoding,raw,logits,['x'],self.config)
        self.assertEqual(result['reason'],'invalid_capture')
        logits['first'][0][0] = float('nan')
        result = correct(self.encoding,raw,logits,['x'],self.config)
        self.assertEqual(result['reason'],'invalid_capture')

    def test_baseline_only_renames_and_ties_by_hash(self):
        first,second = pair(),pair(7)
        request = {'input':{'params':[['n','int']],
            'starter_code':'class Solution:\n    def other(self, n: int) -> int:\n        pass\n'}}
        program,identity,reason = nearest_graph(request,[first,second],[.5,.5],self.encoding)
        expected = min([first,second],key=lambda p:p['graph_sha256'])
        self.assertIsNone(reason); self.assertEqual(identity,expected['graph_sha256'])
        self.assertEqual(program['parameters'],['n'])
        self.assertEqual(typed_program.execute(program,{'n':3}),typed_program.execute(expected['target']['program'],{'x':3}))
        bad = copy.deepcopy(first); bad['learning_split'] = 'development_audit'
        with self.assertRaises(ValueError): nearest_graph(request,[bad],[1.],self.encoding)
        request['input']['starter_code'] = 'class Solution:\n    def other(self, n: bool) -> int:\n        pass\n'
        self.assertEqual(nearest_graph(request,[first],[1.],self.encoding)[2],'no_compatible_training_graph')

    def run_fixture(self, program, verdict=True, shared=.01):
        raw,logits = capture(self.encoding,program)
        def judge(*args,**kwargs):
            return Verdict(verdict,None if verdict else 'wrong_answer',1,int(verdict),.001)
        return run_route('raw',self.problem,raw,logits,self.encoding,'fixture',shared,
                         self.config,2.,judge=judge)

    def test_validity_execution_wrong_acceptance_and_budget_separate(self):
        row = self.run_fixture(graph(7),verdict=False)
        self.assertTrue(row['structurally_valid']); self.assertEqual(row['decision'],'abstain')
        accepted = self.run_fixture(graph(7))
        scored = score_fixed(accepted,self.problem,[{'args':[3],'expected':3}],
            judge=lambda *a,**k:Verdict(False,'wrong_answer',1,0,.01))
        self.assertTrue(scored['wrong_acceptance']); self.assertFalse(scored['accepted_correct'])
        timeout = self.run_fixture(graph(),shared=2.1)
        self.assertTrue(timeout['structurally_valid']); self.assertEqual(timeout['reason'],'decision_budget')
        self.assertIsNone(timeout['public'])

    def test_independent_scoring_does_not_change_public_decision(self):
        row = self.run_fixture(graph(),verdict=False)
        scored = score_fixed(row,self.problem,[{'args':[3],'expected':3}],
            judge=lambda *a,**k:Verdict(True,None,1,1,.01))
        self.assertTrue(scored['independently_correct'])
        self.assertFalse(scored['accepted_correct']); self.assertEqual(scored['decision'],'abstain')
        self.assertNotIn('independent',row)

    def test_missing_or_broken_judge_is_unknown_not_a_wrong_answer(self):
        accepted = self.run_fixture(graph())
        for reason in ('sandbox_error','checker_error','no_tests'):
            with self.subTest(reason=reason):
                scored = score_fixed(accepted,self.problem,[],
                    judge=lambda *a,**k:Verdict(False,reason,0,0,.01))
                self.assertIsNone(scored['independently_correct'])
                self.assertFalse(scored['wrong_acceptance'])
                self.assertFalse(scored['accepted_correct'])
                self.assertTrue(scored['infrastructure_failure'])
                self.assertEqual(correction_outcome(scored,scored),'unknown')

    @unittest.skipUnless(Path('/usr/bin/bwrap').exists() and Path('/usr/bin/prlimit').exists(),
                         'Real execution requires the Linux sandbox')
    def test_real_sandbox_distinguishes_invalid_repaired_and_valid_wrong(self):
        raw,logits = capture(self.encoding,graph())
        corrupt(raw,logits,'first',0,1)
        common = (self.problem,raw,logits,self.encoding,'fixture',.01,self.config,2.)
        unchanged = run_route('raw',*common)
        fixed = run_route('constrained',*common)
        # A constant passes this public example but fails other identity inputs.
        wrong = run_route('nearest_training_graph',*common,baseline_graph=graph(3))
        self.assertFalse(unchanged['structurally_valid'])
        self.assertEqual(unchanged['decision'],'abstain')
        self.assertTrue(fixed['structurally_valid'])
        self.assertEqual(fixed['decision'],'answered',fixed)
        self.assertEqual(wrong['decision'],'answered',wrong)
        independent = [{'args':[n],'expected':n} for n in (-4,0,42)]
        fixed_score = score_fixed(fixed,self.problem,independent)
        wrong_score = score_fixed(wrong,self.problem,independent)
        self.assertTrue(fixed_score['accepted_correct'],fixed_score)
        self.assertTrue(wrong_score['wrong_acceptance'],wrong_score)
        self.assertFalse(wrong_score['accepted_correct'])

    def test_outcomes_and_gate_require_correctness_gain(self):
        def result(valid=False,correct=False,wrong=False,latency=.1):
            return {'structurally_valid':valid,'accepted_correct':correct,'wrong_acceptance':wrong,
                    'independently_correct':correct,'decision':'answered' if correct or wrong else 'abstain',
                    'graph_sha256':'g' if valid else None,'infrastructure_failure':False,
                    'timing':{'total_seconds':latency}}
        abstain, valid, correct_, wrong = result(),result(True),result(True,True),result(True,False,True)
        self.assertEqual(correction_outcome(abstain,valid),'neutral')
        self.assertEqual(correction_outcome(abstain,correct_),'useful')
        self.assertEqual(correction_outcome(correct_,abstain),'harmful')
        self.assertEqual(correction_outcome(abstain,wrong),'harmful')
        self.assertEqual(correction_outcome(abstain,abstain),'unchanged')
        rows = [{'split':split,'routes':{'raw':abstain,'constrained':fixed,'nearest_training_graph':abstain}}
                for split,fixed in [('development_fit',abstain),('development_audit',valid)]]
        self.assertFalse(summarize(rows,CONFIG['selection'])['development_qualified'])
        rows[1]['routes']['constrained'] = correct_
        self.assertTrue(summarize(rows,CONFIG['selection'])['development_qualified'])
        rows[1]['routes']['constrained'] = result(True,True,latency=.5)
        self.assertFalse(summarize(rows,CONFIG['selection'])['development_qualified'])
        rows[1]['routes']['constrained'] = wrong
        self.assertFalse(summarize(rows,CONFIG['selection'])['development_qualified'])


if __name__=='__main__': unittest.main()
