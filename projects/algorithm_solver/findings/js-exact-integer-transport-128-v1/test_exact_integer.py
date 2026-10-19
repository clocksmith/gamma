"""Independent protocol precision fixtures; no problem-specific expected rewrite."""
import json
import unittest
from algsolve.judge import judge,sandbox
import exact_integer as transport

class ExactIntegerTests(unittest.TestCase):
    def run_case(self,source,args,expected,compare='return'):
        tests=[judge.FunctionalTest(args=args,expected=expected,compare=compare)]
        verdict,raw,payload=transport.execute(source,'f',[['p0','value']],tests)
        self.assertNotIn('expected',json.loads(payload))
        self.assertNotIn('expected',json.loads(payload)['calls'][0])
        return verdict,raw

    def test_exact_roundtrip_and_safe_backward_values(self):
        values=[0,1,-1,9007199254740991,-9007199254740991,
                9007199254740992,9007199254740993,-9007199254740993,
                9223372036854775807,-9223372036854775808,10**100,
                1.25,True,None,'hello',[1,9007199254740993],
                {'nested':[9007199254740993,-9007199254740993]}]
        for value in values:
            with self.subTest(value=value):
                verdict,_=self.run_case('function f(x){return x;}',[value],value)
                self.assertTrue(verdict.passed,verdict)

    def test_exact_output_and_adjacent_wrong_integer(self):
        good,raw=self.run_case('function f(){return 9007199254740993n;}',[],9007199254740993)
        self.assertTrue(good.passed);self.assertIn(transport.TAG.encode(),raw.stdout)
        wrong,_=self.run_case('function f(){return 9007199254740992n;}',[],9007199254740993)
        self.assertFalse(wrong.passed);self.assertEqual(wrong.reason,'wrong_answer')
        unsafe,_=self.run_case('function f(){return 9007199254740993;}',[],9007199254740993)
        self.assertFalse(unsafe.passed);self.assertEqual(unsafe.reason,'runtime_error')

    def test_bigint_mutation_and_node_values(self):
        v,_=self.run_case('function f(x){x[0]+=1n;return 0;}',[[9007199254740993]],[9007199254740994],compare='arg:0')
        self.assertTrue(v.passed)
        for marker in ['__tree_node__','__list_node__']:
            value={marker:[9007199254740993,2]}
            with self.subTest(marker=marker):
                v,_=self.run_case('function f(x){return x;}',[value],value)
                self.assertTrue(v.passed,v)

    def test_v1_backward_transport(self):
        samples=[([{'__tree_node__':[1,2,3]}],{'__tree_node__':[1,2,3]}),
                 ([{'__list_node__':[1,2,3]}],{'__list_node__':[1,2,3]}),
                 ([{'__tree_node__':[]}],None),([{'__list_node__':[]}],None),
                 ([[1,2,None]], [1,2,None]),([1.5],1.5)]
        baseline=transport.HARNESS.parents[1]/'source-corpus-js-py-128-v3/return_harness.cjs'
        for args,expected in samples:
            with self.subTest(args=args):
                ts=[judge.FunctionalTest(args=args,expected=expected)]
                calls=json.dumps({'method':'f','params':[['x','value']],'calls':[{'args':args,'capture_args':False}]})
                raw=sandbox.run(['/usr/bin/node','--jitless','--max-old-space-size=64','harness.cjs'],files={'harness.cjs':baseline.read_text(),'candidate.cjs':'function f(x){return x;}','calls.json':calls},limits=sandbox.Limits(wall_seconds=8,cpu_seconds=3,memory_bytes=1024**3,max_output_bytes=65536))
                old=judge._score_functional(raw,ts);new,_=self.run_case('function f(x){return x;}',args,expected)
                self.assertTrue(old.passed);self.assertTrue(new.passed)

    def test_noncanonical_tags_and_reserved_objects(self):
        for text in ['', '+1','01','-0','1.0','1e3',' 1',True,'1'*4097]:
            with self.subTest(text=str(text)[:20]):
                with self.assertRaises(ValueError):transport.unpack_output({transport.TAG:text})
        with self.assertRaises(ValueError):transport.unpack_output({transport.TAG:'1','other':0})
        with self.assertRaises(ValueError):transport.pack_input({transport.TAG:'1'})
        verdict,_=self.run_case('function f(){return {__gamma_bigint_v1__:"9007199254740993"};}',[],9007199254740993)
        self.assertFalse(verdict.passed)

    def test_malformed_raw_output_fail_closed(self):
        values=[b'{"i":0,"result":9007199254740993}\n{"done":1}\n',
                b'{"i":0,"result":1e30}\n{"done":1}\n',
                b'{"i":0,"result":NaN}\n{"done":1}\n',
                b'{"i":0,"result":1,"result":2}\n{"done":1}\n',
                b'{"i":0,"result":{"__gamma_bigint_v1__":"01"}}\n{"done":1}\n']
        for stdout in values:
            with self.subTest(stdout=stdout):
                r=sandbox.SandboxResult(0,None,stdout,b'',0)
                v=transport.score_result(r,[judge.FunctionalTest(expected=1)])
                self.assertFalse(v.passed);self.assertEqual(v.reason,'malformed_output')
        for value in [float('nan'),float('inf'),float(2**53)]:
            with self.assertRaises(ValueError):transport.pack_input(value)

    def test_limits_and_original_failure_priority(self):
        for flag,reason in [('timed_out','timeout'),('output_limit_exceeded','output_limit')]:
            r=sandbox.SandboxResult(1,None,b'incomplete',b'',0,**{flag:True})
            self.assertEqual(transport.score_result(r,[judge.FunctionalTest(expected=1)]).reason,reason)
        with self.assertRaises(ValueError):transport.pack_input(10**4096)

if __name__=='__main__':unittest.main()
