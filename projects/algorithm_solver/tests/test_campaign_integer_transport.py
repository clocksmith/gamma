"""Portable regression cases for exact integer transport and strict booleans."""
import copy,json,unittest
from algsolve import campaign_exact_integer as swap,campaign_633_integer as square
class IntegerTransportTests(unittest.TestCase):
    def raw(self,language='javascript',value=2**64-1):
        tag={swap.TAG:str(value)}
        return [dict(i=0,result=False,args_before=[tag],args_after=[tag],argument_runtime_types=['bigint' if language=='javascript' else 'int'],result_runtime_type='boolean' if language=='javascript' else 'bool',input_object_count=0,returned_input_ids=[],input_node_values_preserved=True),{'done':1}]
    def encode(self,rows):return '\n'.join(swap.compact(row) for row in rows)+'\n'
    def test_uint64_boundary_roundtrip(self):
        for language in ['python','javascript']:
            result=square.decode_stdout(self.encode(self.raw(language)),[{'args':[2**64-1]}],language)
            self.assertEqual(result[0]['args_before'],[2**64-1]);self.assertIs(result[0]['result'],False)
    def test_truthy_numeric_result_rejected(self):
        for value in [0,1,'false',None]:
            rows=self.raw();rows[0]['result']=value
            with self.subTest(value=value),self.assertRaises(ValueError):square.decode_stdout(self.encode(rows),[{'args':[2**64-1]}],'javascript')
    def test_mutation_wrong_type_and_boolean_index_rejected(self):
        for field,value in [('i',False),('input_object_count',False),('argument_runtime_types',['number']),('result_runtime_type','number'),('args_after',[{swap.TAG:'0'}])]:
            rows=self.raw();rows[0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):square.decode_stdout(self.encode(rows),[{'args':[2**64-1]}],'javascript')
    def test_duplicate_json_field_rejected(self):
        raw=self.encode(self.raw()).replace('"result":false','"result":true,"result":false')
        with self.assertRaises(ValueError):square.decode_stdout(raw,[{'args':[2**64-1]}],'javascript')
    def test_overflow_and_noncanonical_decimals_rejected(self):
        for value in ['00','+1','1.0',str(2**64),'-1']:
            with self.subTest(value=value),self.assertRaises(ValueError):square.integer({swap.TAG:value})
    def test_unsafe_number_and_safe_bigint_result_rejected_for_swap(self):
        case={'args':[9007199254740991]};rows=self.raw(value=case['args'][0]);rows[0].update(result={swap.TAG:'9007199254740992'},argument_runtime_types=['number'],result_runtime_type='number')
        with self.assertRaises(ValueError):swap.decode_stdout(self.encode(rows),case)
        rows[0].update(result={swap.TAG:'1'},result_runtime_type='bigint')
        with self.assertRaises(ValueError):swap.decode_stdout(self.encode(rows),case)
if __name__=='__main__':unittest.main()
