import copy
import importlib.util
from pathlib import Path
import unittest

def load(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
h=load('gamma_m_native_harness_test','native_harness.py');p=load('gamma_m_native_protocol_test','native_protocol.py')
class Transport:
    decode=staticmethod(copy.deepcopy);encode=staticmethod(copy.deepcopy);aliases=staticmethod(lambda args,out:[])

class NativeControls(unittest.TestCase):
    def test_constructor_arguments_same_receiver_and_fresh_trace(self):
        class EventManager:
            def __init__(self,events):self.value=events[0][0]
            def updatePriority(self,eventId,newPriority):self.value+=newPriority
            def pollHighest(self):return self.value
        args=[['EventManager','pollHighest','updatePriority','pollHighest'],[[[[2,3],[3,9]]],[],[2,4],[]]]
        for _ in range(2):
            record=h.observe({'EventManager':EventManager},3885,{'args':args},Transport)
            self.assertIsNone(p.check(3885,args,record,[None,2,None,6],'python'))
    def test_no_solve_fallback_or_other_class(self):
        args=[['EventManager'],[[[[1,1]]]]]
        with self.assertRaises(TypeError):h.observe({'solve':lambda *args:[]},3885,{'args':args},Transport)
        for bad in (3881,True):
            with self.assertRaises(ValueError):h.shape(bad,args)
    def test_packet_no_expected_and_bound(self):
        row={'args':[['EventManager','pollHighest'],[[[[1,1]]],[]]],'expected':[None,1]}
        raw=p.packet(3885,[row],maximum_bytes=10000);self.assertNotIn(b'expected',raw)
        with self.assertRaises(ValueError):p.packet(3885,[row],maximum_bytes=1)
    def test_effect_type_receiver_snapshot_rejections(self):
        args=[['EventManager','updatePriority','pollHighest'],[[[[1,1]]],[1,2],[]]];expected=[None,None,1];record=p.projected_record(3885,args,expected,'python',0);self.assertIsNone(p.check(3885,args,record,expected,'python'))
        for key,value in [('native_receiver_count',True),('native_route','solve'),('native_method_return_types',['constructed','int','int']),('args_after',[]),('result',[None,None,True]),('native_method_snapshots',[None,None,2])]:
            bad=copy.deepcopy(record);bad[key]=value;self.assertIsNotNone(p.check(3885,args,bad,expected,'python'))
if __name__=='__main__':unittest.main()
