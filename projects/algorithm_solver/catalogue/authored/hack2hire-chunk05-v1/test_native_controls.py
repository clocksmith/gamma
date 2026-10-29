"""Post-source API/ownership regressions; not part of the pre-source oracle claim."""
from pathlib import Path
import importlib.util
import json
import subprocess
import unittest

HERE = Path(__file__).resolve().parent
ROWS = json.loads((HERE/'contracts.json').read_text())['problems']


def source(key, language):
    row = next(r for r in ROWS if r['key']==key)
    return HERE/language/(row['variant_id']+('.py' if language=='python' else '.js'))


def load(key):
    spec=importlib.util.spec_from_file_location('controls_'+key,source(key,'python'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


class NativeControls(unittest.TestCase):
    def test_python_snapshot_retry_and_atomic_admission(self):
        cache=load('lru').LRUCache(1);value={'rows':[1]};cache.put(7,value);value['rows'][0]=9
        first=cache.get(7);self.assertEqual(first,{'rows':[1]});first['rows'][0]=8;self.assertEqual(cache.get(7),{'rows':[1]})
        retry=load('retry');outcomes=[{'ok':{'x':[1]}}];result=retry.retryOperation(outcomes,1,0,2);result['value']['x'][0]=7;self.assertEqual(outcomes,[{'ok':{'x':[1]}}])
        attempts=[];waits=[];error=RuntimeError('last')
        def fail():attempts.append(1);raise error
        with self.assertRaises(RuntimeError) as caught:retry.retry(fail,3,2,3,waits.append)
        self.assertIs(caught.exception,error);self.assertEqual(len(attempts),3);self.assertEqual(waits,[2,6])
        limiter=load('rate').RateLimiter([[2,10],[1,1]]);self.assertEqual([limiter.allow(t) for t in [0,0,1,2]],[True,False,True,False])
        radix=load('radix').RadixCache();key=[1,2,3];radix.insert(key,9);key[1]=0;radix.insert([1,2],8);self.assertEqual(radix.get([1,2,3]),9)

    def test_javascript_same_native_ownership_controls(self):
        sources={key:str(source(key,'javascript')) for key in ('lru','retry','rate','radix')}
        program=r'''
const assert=require('node:assert/strict'), paths=JSON.parse(process.argv[1]);
const cache=new (require(paths.lru).LRUCache)(1), value={rows:[1]};cache.put(7,value);value.rows[0]=9;
const first=cache.get(7);assert.deepStrictEqual(first,{rows:[1]});first.rows[0]=8;assert.deepStrictEqual(cache.get(7),{rows:[1]});
const retry=require(paths.retry), outcomes=[{ok:{x:[1]}}], result=retry(outcomes,1,0,2);result.value.x[0]=7;assert.deepStrictEqual(outcomes,[{ok:{x:[1]}}]);
const error=new Error('last'), waits=[];let attempts=0;
try{retry.retry(()=>{attempts++;throw error;},3,2,3,n=>waits.push(n));assert.fail('must throw');}catch(e){assert.strictEqual(e,error);}
assert.equal(attempts,3);assert.deepStrictEqual(waits,[2,6]);
const limiter=new (require(paths.rate).RateLimiter)([[2,10],[1,1]]);assert.deepStrictEqual([0,0,1,2].map(t=>limiter.allow(t)),[true,false,true,false]);
const radix=new (require(paths.radix).RadixCache)(), key=[1,2,3];radix.insert(key,9);key[1]=0;radix.insert([1,2],8);assert.equal(radix.get([1,2,3]),9);
'''
        subprocess.run(['node','--jitless','-e',program,json.dumps(sources)],check=True,capture_output=True,text=True,timeout=5)


if __name__ == '__main__':
    unittest.main()
