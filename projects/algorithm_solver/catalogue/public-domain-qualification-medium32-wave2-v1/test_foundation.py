"""Trusted host oracles/protocol fixtures only; no candidate import/execution."""
import copy,itertools,unittest
from oracle import IDS,validate,expected,brute,compare
from cases import build
class Foundation(unittest.TestCase):
 def test_exhaustive_independent_definition_controls(self):
  for n in range(1,7):
   for xs in itertools.product((-1,0,1),repeat=n):self.assertEqual(expected(1567,[list(xs)]),brute(1567,[list(xs)]))
  for n in range(3,9):
   for s in itertools.product('01',repeat=n):self.assertEqual(expected(1573,[''.join(s)]),brute(1573,[''.join(s)]))
  for n in range(2,5):
   for xs in itertools.product((-1,0,2),repeat=n):self.assertEqual(expected(1630,[list(xs),[0],[n-1]]),brute(1630,[list(xs),[0],[n-1]]))
  for n in range(1,8):
   for s in itertools.product('ab',repeat=n):self.assertEqual(expected(1653,[''.join(s)]),brute(1653,[''.join(s)]))
  for n in(2,4,6):
   for xs in itertools.product((1,2,4),repeat=n):self.assertEqual(expected(1877,[list(xs)]),brute(1877,[list(xs)]))
  for n in range(1,6):
   for xs in itertools.product((1,2,3),repeat=n):self.assertEqual(expected(1887,[list(xs)]),brute(1887,[list(xs)]))
  for n in range(1,4):
   for logs in itertools.product(((0,1),(0,2),(1,1),(1,2)),repeat=n):self.assertEqual(expected(1817,[[list(x)for x in logs],3]),brute(1817,[[list(x)for x in logs],3]))
 def test_path_relation_accepts_both_orientations_not_arbitrary_permutation(self):
  for xs in itertools.permutations(range(4)):
   args=[[[a,b]for a,b in zip(xs,xs[1:])]];want=expected(1743,args);valid=brute(1743,args)
   self.assertEqual(len(valid),2)
   for result in valid:
    r={'result':result,'result_type':'list','args_before':args,'args_after':args,'alias_edges':[]}
    self.assertTrue(compare(1743,args,want,r,'python')[0])
   wrong=want[:];wrong[0],wrong[1]=wrong[1],wrong[0]
   r={'result':wrong,'result_type':'list','args_before':args,'args_after':args,'alias_edges':[]};self.assertFalse(compare(1743,args,want,r,'python')[0])
 def test_domains_and_effect_type_omissions(self):
  bad={1567:[[[]],[[10**9+1]]],1573:[['00'],['012']],1630:[[[1,2],[0],[0]],[[1,2],[0,0],[1]],[[1,2],[False],[1]]],1653:[[''],['abc']],1743:[[[[1,1]]],[[[1,2],[2,3],[3,1]]],[[[1,2],[2,1]]],[[[1,2],[3,4]]]],1817:[[[[0,1],[0,2]],1],[[[0,0]],1]],1877:[[[1]],[[0,1]],[[1,2,3]]],1887:[[[0]],[[50001]]]}
  for pid,rows in bad.items():
   for args in rows:
    with self.assertRaises(ValueError):validate(pid,args)
  args=[[1,2,3],[0],[2]];want=expected(1630,args)
  for lang,kind in(('python','list'),('javascript','object')):
   r={'result':[True],'result_type':kind,'args_before':args,'args_after':args,'alias_edges':[]}
   self.assertTrue(compare(1630,args,want,r,lang)[0])
   for key in('result','result_type','args_before','args_after','alias_edges'):
    x=copy.deepcopy(r);x.pop(key);self.assertFalse(compare(1630,args,want,x,lang)[0])
   for key,value in(('result',[1]),('alias_edges',[['result','args.0']]),('args_after',[])):
    x=copy.deepcopy(r);x[key]=value;self.assertFalse(compare(1630,args,want,x,lang)[0])
 def test_all_authored_cases_validate(self):
  rows=build();self.assertEqual(tuple(rows),IDS)
  for pid,cases in rows.items():
   for c in cases:validate(pid,c['args'])
  self.assertTrue(any(len(c['args'][0])==99999 for c in rows[1743]))
 def test_bounded_batches(self):
  import qualify as q
  for pid,rows in build().items():
   groups=list(q.batches(rows));self.assertEqual(sum(len(b)for _,b in groups),len(rows));offset=0
   for at,batch in groups:
    self.assertEqual(at,offset);offset+=len(batch);self.assertLessEqual(len(batch),32)
    self.assertLessEqual(len(q.encoded(q.make_packet(batch))),1800000)
    self.assertLessEqual(1024+sum(q.observation_bound(c)for c in batch),3900000)
  with self.assertRaises(ValueError):list(q.batches([{'args':['a'*1800000],'expected':1}]))
 def test_output_protocol_strictness(self):
  import qualify as q
  for raw in(b'{"i":0}\n{"done":true}\n',b'{"i":0,"i":0}\n{"done":1}\n',b'{"i":0,"result":NaN}\n{"done":1}\n'):
   with self.assertRaises(ValueError):q.parse(raw,1)
  self.assertEqual(q.parse(b'{"i":0}\n{"done":1}\n',1),[{'i':0}])
 def test_code_pins_are_statement_free(self):
  import qualify as q
  from pathlib import Path
  from unittest.mock import patch
  paths=[]
  def read(path):paths.append(path);return b'synthetic code fixture'
  with patch.object(Path,'read_bytes',read):pins=q.pins()
  self.assertTrue(pins);self.assertTrue(paths)
  self.assertTrue(all(p.suffix not in('.json','.md')for p in paths))
 def test_statement_pin_gate_immediately_precedes_each_payload(self):
  import qualify as q
  from pathlib import Path
  from unittest.mock import patch
  events=[];opened=[]
  def gate(pid,*args,**kw):events.append((pid,kw.get('payload_kind')))
  def read(path):
   expected=[int(path.stem)]if path.parent.name=='semantics'else list(IDS)
   self.assertEqual(events,[(f'leetcode:{pid}','statement')for pid in expected])
   events.clear();opened.append(path);return b'synthetic statement fixture'
  with patch('catalogue.boundary_policy.authorize_before_open',gate),patch.object(Path,'read_bytes',read):
   pins=q.statement_pins({'artifact_paths':{},'trusted_hashes':{}})
  self.assertEqual(len(pins),11);self.assertEqual(len(opened),11);self.assertEqual(events,[])
 def test_frozen_sidecar_has_fresh_per_id_statement_gate(self):
  import qualify as q
  from pathlib import Path
  from unittest.mock import patch
  root=Path('/synthetic/freeze');public=Path('/synthetic/public');gatepath=Path('/synthetic/gate.json')
  source=b'# synthetic, never executed';sem=b'{}';gate_raw=q.encoded({'artifact_paths':{},'trusted_hashes':{}})
  cases=q.encoded({str(pid):[]for pid in IDS});events=[];sidecars=[]
  c={'schema':'gamma.public-domain.foundation-medium32-wave2-freeze.v1','ids':list(IDS),'code_sha256':{},'statement_sha256':{},'limits':q.LIMITS,'batch_cases':32,'batch_input_bytes':1800000,'batch_observation_bytes':3900000,'outer_wall_cap_seconds':900,'protected_access':False,'languages':['javascript','python'],'boundary_config_path':str(gatepath),'boundary_config_sha256':q.sha(gate_raw),'public_contract_directory':str(public),'public_contract_manifest_sha256':q.sha(b'{}'),'public_contract_files':[],'official_extraction_sha256':q.sha(b'fixture'),'cases_sha256':q.sha(cases),'sources':{}}
  files={gatepath:gate_raw,public/'manifest.json':b'{}',root/'official-pages.web-extract.txt':b'fixture',root/'public-cases.json':cases}
  for lang,ext in(('javascript','js'),('python','py')):
   for pid in IDS:
    c['sources'][f'{lang}:{pid}']={'id':pid,'language':lang,'path':f'{pid}.{ext}','sha256':q.sha(source),'bytes':len(source),'semantics_sha256':q.sha(sem)}
    files[root/f'{pid}.{ext}']=source;files[root/'semantics'/f'{pid}.json']=sem
  files[root/'contract.json']=q.encoded(c)
  def gate(pid,*args,**kw):events.append((pid,kw.get('payload_kind','source')))
  def read(path):
   if path.parent.name=='semantics':
    self.assertEqual(events[-1],(f'leetcode:{int(path.stem)}','statement'));sidecars.append(path)
   elif path.suffix in('.py','.js'):
    self.assertEqual(events[-1],(f'leetcode:{int(path.stem)}','source'))
   return files[path]
  with patch('catalogue.boundary_policy.authorize_before_open',gate),patch.object(Path,'read_bytes',read),patch.object(q,'pins',return_value={}),patch.object(q,'statement_pins',return_value={}),patch.object(q,'build',return_value={pid:[]for pid in IDS}):
   loaded,_,sources=q.load_freeze(root)
  self.assertEqual(len(sources),16);self.assertEqual(len(sidecars),16)
if __name__=='__main__':unittest.main()
