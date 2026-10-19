import copy
import time
import unittest

from algsolve.synth import typed_recipes as r, typed_program as ir
from algsolve.synth.typed_guard_filter import unreachable_numeric_guard
from algsolve.synth.typed_literal_repair import literal_search
import test_typed_literal_repair as literal_tests


def counter(cutoff=0, reset=2, increment=1, initial=0):
    return r.program({'xs':ir.INTS}, [
        r.assign('i',r.lit(initial),'var'),
        {'op':'for','item':'x','in':r.ref('xs'),'body':[
            {'op':'if','condition':r.pure('lt',r.ref('i'),r.lit(cutoff)),
             'then':[r.assign('i',r.ref('i'),'set')],'else':[]},
            r.assign('i',r.pure('add',r.ref('i'),r.lit(increment)),'set'),
            {'op':'if','condition':r.pure('eq',r.ref('i'),r.lit(reset)),
             'then':[r.assign('i',r.lit(0),'set')],'else':[]}]}],r.ref('i'),'int')


class GuardFilterTests(unittest.TestCase):
    def program(self,*args,**kw):
        p=counter(*args,**kw)
        # Identity write is safe, expressed as +0 to match the deliberately
        # narrow inductive grammar used by the analysis.
        p['body'][1]['body'][0]['then'][0]['value']=r.pure('add',r.ref('i'),r.lit(0))
        ir.validate(p,r.catalog());return p

    def test_nonnegative_counter_makes_zero_cutoff_unreachable(self):
        p=self.program();before=copy.deepcopy(p)
        reason=unreachable_numeric_guard(p)
        self.assertEqual(reason['comparison'],'lt')
        self.assertEqual(reason['lower_bound'],0)
        self.assertEqual(p,before)

    def test_sequential_increment_proves_zero_reset_unreachable(self):
        reason=unreachable_numeric_guard(self.program(cutoff=1,reset=0))
        self.assertEqual(reason['comparison'],'eq')
        self.assertEqual(reason['lower_bound'],1)
        self.assertIsNone(unreachable_numeric_guard(self.program(cutoff=2,reset=3)))

    def test_negative_reset_or_increment_does_not_invent_nonnegative_bound(self):
        self.assertIsNone(unreachable_numeric_guard(self.program(initial=-1)))
        self.assertIsNone(unreachable_numeric_guard(self.program(increment=-1)))
        p=self.program();p['body'][1]['body'][2]['then'][0]['value']=r.lit(-1)
        self.assertIsNone(unreachable_numeric_guard(p))

    def test_unknown_write_invalidates_induction_even_in_nested_branch(self):
        p=self.program();p['body'][1]['body'][2]['then'][0]['value']=r.ref('x')
        self.assertIsNone(unreachable_numeric_guard(p))

    def test_loop_zero_iterations_cannot_inherit_body_only_bound(self):
        p=self.program(cutoff=1)
        p['body'][1]['body']=p['body'][1]['body'][1:2]
        p['body'].append({'op':'if','condition':r.pure('eq',r.ref('i'),r.lit(0)),
                          'then':[r.assign('i',r.lit(0),'set')],'else':[]})
        self.assertIsNone(unreachable_numeric_guard(p))

    def test_filter_skips_public_execution_but_records_proposal(self):
        fixture=literal_tests.LiteralRepairTests();fixture.setUp();seen=[]
        def filtering(graph):
            value=ir.execute(graph,{'x':0})
            return {'reason':'fixture_skip'} if value in (1,2) else None
        def evaluate(graph,seconds):
            value=ir.execute(graph,{'x':0});seen.append(value)
            return dict(passed=value==3,reason=None)
        result=literal_search(fixture.encoding,fixture.codes,fixture.logits,['x'],fixture.config,
                              evaluate,deadline=time.perf_counter()+1,candidate_filter=filtering)
        self.assertEqual(seen,[3]);self.assertEqual(result['executions'],1)
        self.assertEqual(len(result['attempts']),3)
        self.assertIsNotNone(result['attempts'][0]['proposal_filter_failure'])
        self.assertIsNone(result['attempts'][0]['public'])

if __name__=='__main__':unittest.main()
