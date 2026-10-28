import importlib.util
from pathlib import Path
import unittest
S=importlib.util.spec_from_file_location('gamma_v_host_refs',Path(__file__).with_name('oracles.py'));o=importlib.util.module_from_spec(S);S.loader.exec_module(o)
class References(unittest.TestCase):
    def test_public_English_examples_and_zero(self):
        for n,w in [(0,'Zero'),(123,'One Hundred Twenty Three'),(12345,'Twelve Thousand Three Hundred Forty Five'),(1000001,'One Million One'),(2**31-1,'Two Billion One Hundred Forty Seven Million Four Hundred Eighty Three Thousand Six Hundred Forty Seven')]:self.assertEqual(o.expected(273,[n]),w)
    def test_independent_English_decoder_property(self):
        for n in list(range(10000))+[100000,1000000,1000000000,2**31-1]:self.assertEqual(o.decode_english(o.expected(273,[n])),n)
        for s in ('One  Hundred','one','One And One','Zero Thousand','One Thousand One Million'):
            with self.assertRaises(ValueError):o.decode_english(s)
    def test_badversion_boundary_not_solver_bad_argument(self):
        for n in range(1,100):
            for bad in range(1,n+1):
                fixture={'first_bad':bad};self.assertTrue(o.accepts_result(278,[n],bad,fixture))
                if bad<n:self.assertFalse(o.accepts_result(278,[n],bad+1,fixture))
        with self.assertRaises(ValueError):o.validate(278,[5,4],{'first_bad':4})
    def test_real_host_query_response_and_budget(self):
        args=[5];f={'first_bad':4};trace=[{'stage':'solver','version':3,'result':False},{'stage':'solver','version':4,'result':True}];self.assertEqual(o.check_api_trace(278,args,f,trace),(True,None));self.assertFalse(o.check_api_trace(278,args,f,[{'stage':'solver','version':4,'result':False}])[0]);self.assertFalse(o.check_api_trace(278,args,f,trace*3)[0])
    def test_iterator_is_api_object_not_rawlist(self):
        args=[['PeekingIterator','next','peek','peek','next','hasNext'],[[o.ITERATOR_MARKER],[],[],[],[],[]]];f={'iterator0':[1,2]};self.assertEqual(o.expected(284,args,f),[None,1,2,2,2,False])
        with self.assertRaises(ValueError):o.validate(284,[['PeekingIterator'],[[[1,2]]]],f)
    def test_iterator_api_trace_lazy_consumption(self):
        args=[['PeekingIterator','peek','peek','next','hasNext'],[[o.ITERATOR_MARKER],[],[],[],[]]];f={'iterator0':[7]};trace=[{'operation_index':1,'method':'next','result':7},{'operation_index':4,'method':'hasNext','result':False}];self.assertEqual(o.check_api_trace(284,args,f,trace),(True,None));self.assertFalse(o.check_api_trace(284,args,f,[])[0]);self.assertFalse(o.check_api_trace(284,args,f,[{'operation_index':1,'method':'data','result':[7]}])[0])
    def test_exacttypes_and_domains(self):
        self.assertFalse(o.accepts_result(278,[1],True,{'first_bad':1}))
        for pid,args,f in [(273,[-1],None),(278,[0],{'first_bad':1}),(284,[['PeekingIterator','next','next'],[[o.ITERATOR_MARKER],[],[]]],{'iterator0':[1]})]:
            with self.assertRaises(ValueError):o.validate(pid,args,f)
    def test_full_generated_hostonly_population(self):
        import copy
        spec=importlib.util.spec_from_file_location('gamma_v_test_cases',Path(__file__).with_name('cases.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);data=c.build_cases();self.assertEqual(sum(map(len,data.values())),14016)
        for pid,rows in data.items():
            for row in rows:
                before=copy.deepcopy(row);fixture=row.get('host_api_fixture');self.assertTrue(o.accepts_result(pid,row['args'],row['expected'],fixture));self.assertTrue(o.exact(before,row))
                if pid==278:self.assertEqual(len(row['args']),1);self.assertNotIn('first_bad',c.encoded(row['args']).decode())
                if pid==284:self.assertTrue(o.exact(row['args'][1][0],[o.ITERATOR_MARKER]));self.assertNotIn('iterator0',row['args'][1][0][0].keys())
    def test_premium_fixed_membership(self):
        self.assertEqual(set(o.REQUESTED_IDS)-set(o.IDS),set(o.BLOCKED_IDS))
        for pid in o.BLOCKED_IDS:
            with self.assertRaises(ValueError):o.validate(pid,[])
if __name__=='__main__':unittest.main()
