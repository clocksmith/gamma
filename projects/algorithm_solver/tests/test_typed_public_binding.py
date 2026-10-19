import copy
import unittest
from pathlib import Path

from algsolve.synth import typed_codec,typed_program as ir,typed_recipes as r
from algsolve.synth.typed_prediction_codec import PredictionCodec,OPS
from algsolve.synth.typed_public_binding import bind_absent_return,run_public_bound_route
from algsolve.synth.typed_comparison import run_route
from algsolve.records import Problem
from test_typed_comparison import capture,CONFIG

STATEMENT='Return the selected value. If there is no such value, return -1.'
def program():
    return r.program({'x':'int'},[r.assign('answer',r.lit(1),'var'),
        r.branch(r.pure('lt',r.lit(0),r.ref('x')),[r.assign('answer',r.lit(5),'set')])],r.ref('answer'),'int')

class PublicBindingTests(unittest.TestCase):
    def test_exact_public_clause_binds_only_return_initializer(self):
        p=program();before=copy.deepcopy(p);binding=bind_absent_return(p,STATEMENT)
        self.assertEqual(binding['before'],1);self.assertEqual(binding['after'],-1)
        self.assertEqual(p,before)
        self.assertEqual(binding['graph']['body'][1],p['body'][1])
        self.assertEqual(ir.execute(binding['graph'],{'x':-1}),-1)

    def test_examples_quotes_and_conflicting_returns_are_not_authority(self):
        for text in ['Example 1: '+STATEMENT,'"If there is no such value, return -1."',
                     STATEMENT+' Otherwise return 0.','Return -1 if missing.',
                     'Do not return -1. '+STATEMENT]:
            with self.subTest(text=text):self.assertIsNone(bind_absent_return(program(),text))

    def test_reads_or_unconditional_updates_disable_binding(self):
        p=program();p['body'][1]['condition']=r.pure('eq',r.ref('answer'),r.lit(1))
        self.assertIsNone(bind_absent_return(p,STATEMENT))
        p=program();p['body'].append(r.assign('answer',r.lit(8),'set'))
        self.assertIsNone(bind_absent_return(p,STATEMENT))
        p=program();p['body']=p['body'][:1]
        self.assertIsNone(bind_absent_return(p,STATEMENT))

    def test_real_public_route_keeps_contract_binding_while_model_repairs_other_literal(self):
        p=program();encoding=PredictionCodec.fit([dict(learning_split='development_fit',target=typed_codec.encode(p,'fixture'))])
        codes,logits=capture(encoding,p)
        logits['bits']=[[10. if b else -10. for b in row] for row in codes['bits']]
        literals=[i for i,v in enumerate(codes['op']) if OPS[v]=='int']
        value_slot=literals[-1]
        logits['bits'][value_slot][1]=.1;logits['bits'][value_slot][2]=-.2
        identity=typed_codec.frozen(Path(__file__).parents[1]/'contracts/typed_codec_v1.json')
        problem=Problem('fixture','fixture','1','','',STATEMENT,'functional',params=[['x','int']],
            entry={'class':'Solution','method':'solve'},public_tests=[dict(args=[1],expected=6),dict(args=[-1],expected=-1)])
        control=run_route('constrained',problem,codes,logits,encoding,identity,0.,CONFIG['correction'],2.)
        self.assertEqual(control['reason'],'public_failure')
        result=run_public_bound_route(control,problem,logits,encoding,identity,
                                    dict(pool_size=8,max_edits=2,max_executions=4,wall_seconds=.25),2.)
        self.assertEqual(result['decision'],'answered',result['reason'])
        self.assertEqual(result['public_literal_binding']['after'],-1)
        self.assertLessEqual(result['semantic_repair']['executions'],4)
        self.assertEqual(result['raw_codes'],codes)
        slot=result['public_literal_binding']['slot']
        self.assertTrue(all(e['slot']!=slot for a in result['semantic_repair']['attempts'] for e in a['edits']))

    def test_captured_logits_cannot_be_changed_outside_bound_slot(self):
        import time
        from algsolve.synth.typed_literal_repair import literal_search
        p=program();encoding=PredictionCodec.fit([dict(learning_split='development_fit',target=typed_codec.encode(p,'fixture'))])
        codes,_=capture(encoding,p);original=copy.deepcopy(codes['bits'])
        logits=[[10. if b else -10. for b in row] for row in original]
        slot=next(i for i,v in enumerate(codes['op']) if OPS[v]=='int');codes['bits'][slot][0]=1
        result=literal_search(encoding,codes,logits,['x'],dict(pool_size=8,max_edits=2,max_executions=4,wall_seconds=.25),
                              lambda *a:self.fail('must not execute'),deadline=time.perf_counter()+1,
                              captured_bits=original,frozen_slots=())
        self.assertEqual(result['reason'],'invalid_literal_capture')

if __name__=='__main__':unittest.main()
