import copy
import importlib.util
from pathlib import Path
import unittest

def load(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
h=load('gamma_r22b_native_harness_test','native_harness.py');p=load('gamma_r22b_native_protocol_test','native_protocol.py')
class Transport:
    decode=staticmethod(copy.deepcopy);encode=staticmethod(copy.deepcopy);aliases=staticmethod(lambda args,out:[])

class NativeControls(unittest.TestCase):
    def test_constructor_arguments_same_receiver_and_fresh_trace(self):
        class WordFilter:
            def __init__(self,words):self.value=len(words)
            def f(self,pref,suff):self.value+=1;return self.value
        args=[['WordFilter','f','f'],[[['ab','cd']],['a','b'],['c','d']]]
        for _ in range(2):
            record=h.observe({'WordFilter':WordFilter},745,{'args':args},Transport)
            self.assertIsNone(p.check(745,args,record,[None,3,4],'python'))
    def test_no_solve_fallback_or_other_class(self):
        args=[['WordFilter'],[[['a']]]]
        with self.assertRaises(TypeError):h.observe({'solve':lambda *args:[]},745,{'args':args},Transport)
        for bad in (749,True):
            with self.assertRaises(ValueError):h.shape(bad,args)
    def test_packet_no_expected_and_bound(self):
        row={'args':[['WordFilter','f'],[[['ab']],['a','b']]],'expected':[None,0]}
        raw=p.packet(745,[row],maximum_bytes=10000);self.assertNotIn(b'expected',raw)
        with self.assertRaises(ValueError):p.packet(745,[row],maximum_bytes=1)
    def test_effect_type_receiver_snapshot_rejections(self):
        args=[['WordFilter','f','f'],[[['ab']],['a','b'],['b','a']]];expected=[None,0,-1];record=p.projected_record(745,args,expected,'python',0);self.assertIsNone(p.check(745,args,record,expected,'python'))
        for key,value in [('native_receiver_count',True),('native_route','solve'),('native_method_return_types',['constructed','bool','int']),('args_after',[]),('result',[None,False,-1]),('native_method_snapshots',[None,0,0])]:
            bad=copy.deepcopy(record);bad[key]=value;self.assertIsNotNone(p.check(745,args,bad,expected,'python'))
if __name__=='__main__':unittest.main()
