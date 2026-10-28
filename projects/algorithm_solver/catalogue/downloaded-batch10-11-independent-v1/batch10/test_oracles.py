import unittest,itertools,sys,subprocess,os
from pathlib import Path
import oracles as o
class ReferenceTests(unittest.TestCase):
 def test_clock(self):
  self.assertEqual(o.expected(1344,[12,0]),0.0);self.assertEqual(o.expected(1344,[3,30]),75.0);self.assertTrue(o.matches(1344,[],75,75.0));self.assertFalse(o.matches(1344,[],True,1.0));self.assertFalse(o.matches(1344,[],float('nan'),0))
 def test_break_thresholds(self):
  for n in range(1,4):
   for a in itertools.product('abc',repeat=n):
    for b in itertools.product('abc',repeat=n):
     want=any(all(x>=y for x,y in zip(a,p))or all(x<=y for x,y in zip(a,p))for p in itertools.permutations(b));self.assertEqual(o.expected(1433,[''.join(a),''.join(b)]),want)
 def test_entities_and_frogs(self):
  self.assertEqual(o.expected(1410,['&amp;gt; &lt; &&amp;']),'&gt; < &&');self.assertEqual(o.frog_min('croak'),1);self.assertEqual(o.frog_min('ccrrooaakk'),2);self.assertEqual(o.frog_min('croakcrook'),-1)
 def test_family_geometry(self):
  self.assertEqual(o.expected(1386,[1,[[1,1]]]),2);self.assertEqual(o.expected(1386,[1,[[1,2],[1,9]]]),1);self.assertEqual(o.expected(1386,[1,[[1,4],[1,6]]]),0)
 def test_effect_alias_controls(self):
  a=[[[1]]];row={'result':[[1]],'result_type':'list','args_before':a,'args_after':a,'alias_edges':[['result','args.0']]};self.assertEqual(o.compare(1329,a,[[1]],row,'python'),(False,'mutable_alias'));row['alias_edges']=[];row['args_after']=[[[2]]];self.assertEqual(o.compare(1329,a,[[1]],row,'python'),(False,'input_effects'))
 def test_lf_record_framing(self):
  import qualify,json
  row={'i':0,'result':'a\x85b\u2028c','result_type':'string','args_before':['a\x85b\u2028c'],'args_after':['a\x85b\u2028c'],'alias_edges':[]}
  raw=(json.dumps(row,ensure_ascii=False)+'\n'+json.dumps({'done':1})+'\n').encode()
  self.assertEqual(qualify.parse(raw,1),[row])
  with self.assertRaises(ValueError):qualify.parse(raw[:-1],1)
 def test_seed_determinism(self):
  code='import cases,json,hashlib;print(hashlib.sha256(json.dumps(cases.build(),sort_keys=True).encode()).hexdigest())';out=[subprocess.check_output([sys.executable,'-c',code],cwd=Path(__file__).parent,env=dict(os.environ,PYTHONHASHSEED=str(seed)))for seed in (1,2)];self.assertEqual(*out)
if __name__=='__main__':unittest.main()
