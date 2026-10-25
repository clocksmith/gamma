import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).parent
SPEC=importlib.util.spec_from_file_location('frozen_eval_test',HERE/'evaluate.py');e=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(e)

class EvalTests(unittest.TestCase):
    def test_binding_includes_text_order_and_encoder_identity(self):
        rows=[{'problem_id':'a','text':'synthetic A'},{'problem_id':'b','text':'synthetic B'}]
        self.assertNotEqual(e.binding({'model':'one'},rows),e.binding({'model':'two'},rows))
        self.assertNotEqual(e.binding({},rows),e.binding({},rows[::-1]))
        self.assertNotEqual(e.binding({},rows),e.binding({},[dict(rows[0],text='changed'),rows[1]]))
    def test_hash_tamper_rejected(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'fixture.json';p.write_text('{"synthetic":1}');pin={'path':str(p),'sha256':e.sha(p)}
            self.assertEqual(e.read(pin),{'synthetic':1});p.write_text('{"synthetic":2}')
            with self.assertRaises(ValueError):e.read(pin)
    def test_no_raw_query_spans_in_projection(self):
        d={'status':'abstain','query_analysis':{'facts':{'result_shape':'string'},'unsupported_spans':[{'span':'DO_NOT_EXPORT'}],'grammar_complete':False},'guard':{'overall':'unknown','contradictions':[]}}
        result=e.compact(d,'synthetic1');self.assertNotIn('DO_NOT_EXPORT',json.dumps(result));self.assertEqual(result['unsupported_span_count'],1)
    def test_score_roundoff_excluded_but_identity_bound(self):
        one={'status':'accepted','problem_id':'a','implementations':{'x':'exact'},'cosine':.9}
        two=dict(one,cosine=.90000001)
        self.assertEqual(e.decision_projection(one),e.decision_projection(two))
        self.assertNotEqual(e.decision_projection(one),e.decision_projection(dict(two,problem_id='b')))
    def test_missing52query_population_rejected_before_cache(self):
        with self.assertRaises(ValueError):e.restore_queries({},[],None,None)
    def test_baseline_drift_blocks_guard_calls(self):
        class Guard:
            def guarded_decide(self,*args,**kwargs):raise AssertionError('guard must not run')
        policies=[{'id':str(i),'min_cosine':.5,'min_margin':.1}for i in range(20)]
        history={p['id']:{'policy':p,'decisions':[{'status':'accepted','problem_id':'wrong'}]}for p in policies}
        with patch('projects.algorithm_solver.catalogue.empirical_recognition.decide',return_value={'status':'abstain','reason':'synthetic'}):
            with self.assertRaisesRegex(ValueError,'baseline decision drift'):
                e.compare_policies([{'text':'fixture'}],[[]],policies,None,Guard(),[],{},[False],history)
    def test_unchanged20_policy_metrics_and_veto_only(self):
        from projects.algorithm_solver.catalogue.empirical_recognition import score_decisions
        policies=[{'id':str(i),'min_cosine':.5,'min_margin':.1}for i in range(20)]
        q=[{'query_id':'synthetic','text':'owned fixture','kind':'positive','expected_id':'a'}]
        before={'status':'accepted','problem_id':'a','implementations':{'python':'synthetic'}}
        after={'status':'abstain','reason':'description_facet_conflict','query_analysis':{'facts':{},'grammar_complete':False}}
        history={p['id']:{'policy':p,'decisions':[before],'metrics':score_decisions(q,[before])}for p in policies}
        class Guard:
            def guarded_decide(self,*args,**kw):return after
        with patch('projects.algorithm_solver.catalogue.empirical_recognition.decide',return_value=before):
            results,selected=e.compare_policies(q,[[]],policies,None,Guard(),[],{},[False],history)
        self.assertEqual(len(results),20);self.assertEqual(results[0]['metric_deltas']['correct_accepts'],-1)
        self.assertEqual(results[0]['metrics']['abstentions'],1)
    def test_veto_must_not_substitute_identity(self):
        from projects.algorithm_solver.catalogue.empirical_recognition import score_decisions
        policies=[{'id':str(i),'min_cosine':.5,'min_margin':.1}for i in range(20)]
        q=[{'query_id':'synthetic','text':'owned fixture','kind':'positive','expected_id':'a'}]
        before={'status':'accepted','problem_id':'a','implementations':{}}
        history={p['id']:{'policy':p,'decisions':[before],'metrics':score_decisions(q,[before])}for p in policies}
        class Guard:
            def guarded_decide(self,*args,**kw):return dict(before,problem_id='b')
        with patch('projects.algorithm_solver.catalogue.empirical_recognition.decide',return_value=before):
            with self.assertRaisesRegex(ValueError,'veto-only'):e.compare_policies(q,[[]],policies,None,Guard(),[],{},[False],history)

if __name__=='__main__':unittest.main()
