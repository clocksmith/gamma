import json
import unittest

import cases
import protocol as p


def native_record(before,after,kind='void'):
    return {'i':0,'result_type':'dict','result':{'observed_return_kind':kind},
            'args_before':before,'args_after':after,'alias_edges':[]}


class NativeContracts(unittest.TestCase):
    def test_effects_are_not_substituted_by_a_return_value(self):
        case={'args':[[0,1]],'expected':[1,0],'requires_native_effect_change':True}
        self.assertEqual(p.native_effect(case,native_record(case['args'],case['args'],'list'),'python',283),
                         (False,False,'native_argument_effect'))
        self.assertEqual(p.native_effect(case,native_record(case['args'],[[1,0]]),'python',283),
                         (True,True,None))

    def test_degenerate_original_control_is_allowed_to_conform(self):
        values=[{'args':[[0,1]],'expected':[1,0],'requires_native_effect_change':True},
                {'args':[[1,0]],'expected':[1,0],'requires_native_effect_change':False}]
        records=[native_record(values[0]['args'],values[0]['args'],'list'),
                 dict(native_record(values[1]['args'],values[1]['args'],'list'),i=1)]
        raw=b'\n'.join(json.dumps(r).encode() for r in records)+b'\n{"done":2}\n'
        unit={'problem_id':283,'language':'python','mode':'native_void','negative_control':True}
        counts,failures=p.evaluate(unit,values,[0,1],{'exit_code':0,'timed_out':False,'output_limit_exceeded':False},raw)
        self.assertEqual(counts['effect_conforming_rows'],1)
        self.assertEqual(counts['degenerate_effect_conforming_rows'],1)
        self.assertEqual(counts['nontrivial_mutation_rejections'],1)
        self.assertEqual(counts['void_return_rows'],0)
        self.assertEqual(failures,[{'case':0,'reason':'native_argument_effect'}])

    def test_selected_void_promise_is_a_separate_check(self):
        values=[{'args':[[1,0]],'expected':[1,0],'requires_native_effect_change':False}]
        record=native_record(values[0]['args'],values[0]['args'],'list')
        raw=json.dumps(record).encode()+b'\n{"done":1}\n'
        unit={'problem_id':283,'language':'python','mode':'native_void','negative_control':False}
        counts,failures=p.evaluate(unit,values,[0],{'exit_code':0,'timed_out':False,'output_limit_exceeded':False},raw)
        self.assertEqual(counts['effect_conforming_rows'],1)
        self.assertEqual(failures,[{'case':0,'reason':'declared_void_not_observed'}])

    def test_wiggle_freedom_and_multiset(self):
        args=[[1,5,1,1,6,4]];want=sorted(args[0])
        self.assertTrue(cases.post_matches(324,args,[[1,6,1,5,1,4]],want))
        self.assertTrue(cases.post_matches(324,args,[[1,4,1,5,1,6]],want))
        self.assertFalse(cases.post_matches(324,args,args,want))
        self.assertFalse(cases.post_matches(324,args,[[1,6,1,6,1,4]],want))

    def test_alias_and_unrelated_argument_rejection(self):
        case={'args':[[1,2,3],1],'expected':[3,1,2],'requires_native_effect_change':True}
        record=native_record(case['args'],[[3,1,2],1])
        self.assertEqual(p.native_effect(case,record,'python',189),(True,True,None))
        self.assertEqual(p.native_effect(case,dict(record,args_after=[[3,1,2],2]),'python',189),(False,True,'native_argument_effect'))
        self.assertEqual(p.native_effect(case,dict(record,alias_edges=[['args.0.0','args.0.1']]),'python',189),(False,True,'native_argument_alias'))

    def test_partial_streams_are_not_completed_call_slots(self):
        record={'i':0,'result':321,'result_type':'int','args_before':[123],'args_after':[123],'alias_edges':[]}
        raw=json.dumps(record).encode()+b'\n{"i":1'
        unit={'problem_id':7,'language':'python','mode':'native_value','negative_control':False}
        values=[{'args':[123],'expected':321},{'args':[456],'expected':654}]
        counts,failures=p.evaluate(unit,values,[0,1],{'exit_code':137,'timed_out':False,'output_limit_exceeded':False},raw)
        self.assertEqual(counts['requested_call_slots'],2)
        self.assertEqual(counts['complete_observation_rows'],1)
        self.assertEqual(counts['successful_complete_streams'],0)
        self.assertEqual(failures[-1]['batch_failure'],'sandbox_process_failure')

    def test_named_entry_is_distinct_from_class_compatibility(self):
        planned=p.units()
        named=[u for u in planned if u['entry_form']=='named' and not u['negative_control']]
        self.assertEqual(len(named),5)
        for unit in named:
            method=p.selection()[(unit['problem_id'],'javascript')]['method']
            self.assertIn((method+'(...args)').encode(),p.adapter(unit))
            self.assertNotIn(b'new Solution()',p.adapter(unit))
        for unit in planned:
            if unit['negative_control']:
                self.assertEqual(unit['entry_form'],'class' if unit['language']=='python' else 'named')

    def test_native_domain_rejections(self):
        for pid,args in ((189,[[],0]),(189,[[1],-1]),(283,[[0]*10001]),(289,[[[0]]*26]),(324,[[-1,2]]),(344,[['é']])):
            with self.subTest(pid=pid),self.assertRaises(AssertionError):cases.validate_native(pid,args)


if __name__=='__main__':unittest.main()
