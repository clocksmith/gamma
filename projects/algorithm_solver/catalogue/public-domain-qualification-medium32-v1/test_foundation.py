"""Trusted host controls only. Never execute/import incoming candidates."""
import copy,itertools,unittest
from oracle import IDS,validate,expected,brute,compare
from cases import build
class Foundation(unittest.TestCase):
 def test_small_definition_controls(self):
  for n in range(1,6):
   for xs in itertools.product((1,2),repeat=n):
    for k in range(1,n+1):self.assertEqual(expected(1248,[list(xs),k]),brute(1248,[list(xs),k]))
  for n in(2,4,6):
   for xs in itertools.product((1,2,3),repeat=n):self.assertEqual(expected(1338,[list(xs)]),brute(1338,[list(xs)]))
  for n in range(1,5):
   for s in itertools.product('ab',repeat=n):
    for k in range(1,n+2):self.assertEqual(expected(1400,[''.join(s),k]),brute(1400,[''.join(s),k]))
  for n in range(1,5):
   for xs in itertools.product((-1,0,1),repeat=n):
    for k in range(1,n+1):self.assertEqual(sorted(expected(1471,[list(xs),k])),sorted(brute(1471,[list(xs),k])))
   for xs in itertools.product((1,3),repeat=n):
    for k in range(1,n+1):
     for m in range(1,4):self.assertEqual(expected(1482,[list(xs),m,k]),brute(1482,[list(xs),m,k]))
  for n in range(1,4):
   words=[''.join(w)for w in itertools.product('az',repeat=n)]
   for s,t in itertools.product(words,repeat=2):
    for k in(0,1,25,26,27,52):self.assertEqual(expected(1540,[s,t,k]),brute(1540,[s,t,k]))
 def test_graph_rewire_and_reversal_bruteforce(self):
  for n in range(2,5):
   edges=list(itertools.combinations(range(n),2))
   for mask in range(1,1<<len(edges)):
    es=[list(e)for i,e in enumerate(edges)if mask>>i&1]
    self.assertEqual(expected(1319,[n,es]),brute(1319,[n,es]))
   for parents in itertools.product(*[range(i)for i in range(1,n)]):
    es=[(i+1,p)for i,p in enumerate(parents)]
    for flip in itertools.product((0,1),repeat=n-1):
     args=[n,[[v,u]if b else[u,v]for(u,v),b in zip(es,flip)]]
     self.assertEqual(expected(1466,args),brute(1466,args))
 def test_exact_domains_and_no_silent_relaxation(self):
  bad={1248:[[[0],1],[[1],0],[[1],True]],1319:[[1,[]],[2,[]],[2,[[0,1],[1,0]]],[3,[[0,0]]]],1338:[[[1]],[[1,2,3]],[[0,1]]],1400:[['A',1],['',1],['a',0]],1466:[[3,[[0,1],[1,0]]],[3,[[0,1]]]],1471:[[[0],0],[[100001],1]],1482:[[[0],1,1],[[1],0,1],[[1],1,0]],1540:[['A','a',1],['a','a',-1],['a','a',10**9+1]]}
  for pid,rows in bad.items():
   for args in rows:
    with self.assertRaises(ValueError):validate(pid,args)
  validate(1400,['a',100000]);validate(1540,['a','aa',0])
 def test_multiset_types_effects_and_omissions(self):
  args=[[1,1,3,5,5],2];want=expected(1471,args)
  for language,kind in(('python','list'),('javascript','object')):
   r={'result':[5,5],'result_type':kind,'args_before':args,'args_after':args,'alias_edges':[]}
   self.assertTrue(compare(1471,args,want,r,language)[0])
   for field in('result','result_type','args_before','args_after','alias_edges'):
    x=copy.deepcopy(r);x.pop(field);self.assertFalse(compare(1471,args,want,x,language)[0])
   for val in([5],[5,3],[5,True],[5.0,5]):
    x=copy.deepcopy(r);x['result']=val;self.assertFalse(compare(1471,args,want,x,language)[0])
   x=copy.deepcopy(r);x['alias_edges']=[['result','args.0']];self.assertFalse(compare(1471,args,want,x,language)[0])
  args=[[1,2,3,4,5],2];want=expected(1471,args)
  self.assertTrue(compare(1471,args,want,{'result':[1,5],'result_type':'list','args_before':args,'args_after':args,'alias_edges':[]},'python')[0])
  args=['aa',1];want=expected(1400,args)
  self.assertFalse(compare(1400,args,want,{'result':1,'result_type':'int','args_before':args,'args_after':args,'alias_edges':[]},'python')[0])
 def test_case_build_domain_and_maxima(self):
  rows=build();self.assertEqual(tuple(rows),IDS)
  for pid,cs in rows.items():
   self.assertGreater(len(cs),1)
   for c in cs:validate(pid,c['args'])
  self.assertTrue(any(c['args'][0]==100000 for c in rows[1319]))
  self.assertTrue(any(len(c['args'][0])==100000 and c['args'][1]==100000 for c in rows[1471]))
 def test_bounded_batches_cover_all_cases_and_large_singletons(self):
  import qualify as q
  cases=build()
  for pid,rows in cases.items():
   parts=list(q.batches(rows));self.assertEqual(sum(len(b)for _,b in parts),len(rows));offset=0
   for at,batch in parts:
    self.assertEqual(at,offset);offset+=len(batch);self.assertLessEqual(len(batch),32)
    self.assertLessEqual(len(q.encoded(q.make_packet(batch))),1800000)
    self.assertLessEqual(1024+sum(q.observation_bound(c)for c in batch),3900000)
  case={'args':[[100000]*100000,100000],'expected':[100000]*100000}
  self.assertEqual(len(list(q.batches([case,case]))),2)
  with self.assertRaises(ValueError):list(q.batches([{'args':['a'*1800000],'expected':True}]))
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
  c={'schema':'gamma.public-domain.foundation-medium32-wave1-freeze.v1','ids':list(IDS),'code_sha256':{},'statement_sha256':{},'limits':q.LIMITS,'batch_cases':32,'batch_input_bytes':1800000,'batch_observation_bytes':3900000,'outer_wall_cap_seconds':900,'protected_access':False,'languages':['javascript','python'],'boundary_config_path':str(gatepath),'boundary_config_sha256':q.sha(gate_raw),'public_contract_directory':str(public),'public_contract_manifest_sha256':q.sha(b'{}'),'public_contract_files':[],'official_extraction_sha256':q.sha(b'fixture'),'cases_sha256':q.sha(cases),'sources':{}}
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
