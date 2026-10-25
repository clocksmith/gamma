"""Host-only checks: inert fixture records; no candidate execution."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import qualify as q

class ReplayTests(unittest.TestCase):
    def test_inputs_only_packet(self):
        packet=q.packet('solve',[{'args':[[1,2]],'expected':99,'compare':'return','validator':'secret'}])
        self.assertEqual(packet['calls'],[{'args':[[1,2]]}])
        self.assertNotIn('expected',json.dumps(packet))
    def test_typed_and_inexact_inputs_blocked(self):
        for value in ({'__list_node__':[1]},2**53,float(2**53),{'x':1},float('inf'),float('nan')):
            self.assertFalse(q.plain(value))
        self.assertTrue(q.plain([None,True,4,'x',1.5,[]]))
    def test_output_protocol(self):
        self.assertEqual(q.parse(b'{"i":0,"result":1}\n{"done":1}\n',1)[0]['result'],1)
        for raw in (b'{"i":0,"i":0}\n{"done":1}',b'{"i":true}\n{"done":1}',b'{"i":0}\n{"done":true}',b'{"i":0,"result":NaN}\n{"done":1}',b'{"done":1}',b'{"i":1}\n{"done":1}'):
            with self.assertRaises((ValueError,TypeError)):q.parse(raw,1)
    def test_strict_return_types_and_errors(self):
        self.assertFalse(q.matches({'args':[],'expected':1},{'result':True}))
        self.assertFalse(q.matches({'args':[],'expected':1},{'result':1,'error':'failure'}))
        self.assertTrue(q.matches({'args':[],'expected':[[1],[2]],'compare':'return:unordered_outer'},{'result':[[2],[1]]}))
        self.assertFalse(q.matches({'args':[],'expected':1,'compare':'unknown'},{'result':1}))
    def test_original_float_tolerance_not_exact_or_unbounded(self):
        case={'args':[],'expected':0.7327777870686082}
        self.assertTrue(q.matches(case,{'result':0.7327777870686083}))
        self.assertFalse(q.matches(case,{'result':0.733}))
        self.assertFalse(q.matches(case,{'result':True}))
        self.assertFalse(q.matches(case,{'result':float('nan')}))
    def test_effects_require_values_aliases_and_identity_survival(self):
        row={'args_after':[[1]],'alias_paths':[],'identity_survival':[[['arg/0'],['arg/0']]]}
        self.assertTrue(q.effects_match(row,dict(row)))
        for key,value in [('args_after',[[2]]),('alias_paths',[['arg/0','result']]),('identity_survival',[[['arg/0'],[]]])]:
            self.assertFalse(q.effects_match({**row,key:value},row))
        self.assertFalse(q.effects_match({'args_after':[[1]]},row))
    def test_outside_partition_rejected_before_private_reads(self):
        transfer=q.load_module('paired_test_transfer',q.PILOT/'transfer.py')
        with patch.object(transfer,'read_relative',side_effect=AssertionError('private read')):
            # derive_manifest needs public reads, so substitute pinned policy for this guard test.
            with patch.object(transfer,'derive_manifest',return_value={'partition':{'dev_fit':list(range(300))}}):
                with patch.object(q,'load_module',return_value=transfer):
                    with self.assertRaisesRegex(ValueError,'outside frozen'):q.inputs(Path('/not-used'),[9000])
    def test_runners_compile_without_execution(self):
        compile(q.PYTHON_RUNNER,'runner.py','exec')
        self.assertNotIn('expected',q.PYTHON_RUNNER)
        self.assertNotIn('expected',q.JAVASCRIPT_RUNNER)

if __name__=='__main__':unittest.main()
