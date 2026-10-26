import copy,hashlib,json,pathlib,tempfile,unittest
from representation import clauses,load_authority
from aggregate import aggregate
class Tests(unittest.TestCase):
 def setUp(self):
  self.a={'problem_id':'p1','fields':{'output':'Return an input index.'},'clauses':[{'role':'output_identity','polarity':1,'field':'output','span':[0,22],'required':True}]};self.c=clauses(self.a,'a'*64);self.q=[{'evidence_id':'q1','role':'output_identity','polarity':1,'scope':'explicit'}];self.sim={('q1',self.c[0]['clause_id']):.8}
 def run_case(self,q=None,cs=None,sim=None):return aggregate(['p1','p2'],[.8,.7],{'p1':self.c if cs is None else cs},self.q if q is None else q,self.sim if sim is None else sim,2)
 def test_exact_span(self):
  self.assertEqual(self.c[0]['text'],'Return an input index.');self.assertEqual(self.c[0]['field_sha256'],hashlib.sha256(self.a['fields']['output'].encode()).hexdigest())
 def test_duplicate_clause_invariance(self):self.assertEqual(self.run_case(),self.run_case(cs=self.c*3))
 def test_duplicate_evidence_invariance(self):self.assertEqual(self.run_case(),self.run_case(q=self.q*3))
 def test_negation_sign(self):
  q=copy.deepcopy(self.q);q[0]['polarity']=-1;self.assertEqual(self.run_case(q=q)['rows'][0]['empirical_compatibility_signal'],-.8)
 def test_unknown_omission_not_false(self):
  r=self.run_case(q=[],sim={})['rows'];self.assertIsNone(r[0]['empirical_compatibility_signal']);self.assertEqual(r[0]['unknown_required_roles'],['output_identity']);self.assertEqual(r[1]['authority_status'],'UNKNOWN');self.assertEqual([x['problem_id']for x in r],['p1','p2'])
 def test_scope_uncertainty(self):
  q=copy.deepcopy(self.q);q[0]['scope']='conditional_unresolved';r=self.run_case(q=q,sim={});self.assertEqual(r['ignored_scope_evidence'],['q1']);self.assertIsNone(r['rows'][0]['empirical_compatibility_signal'])
 def test_conflict_unknown(self):
  q=copy.deepcopy(self.q);q[0]['polarity']=-1;r=self.run_case(q=self.q+q,sim={});self.assertEqual(r['conflicted_evidence'],['q1']);self.assertIsNone(r['rows'][0]['empirical_compatibility_signal'])
 def test_composition_permutation(self):
  a=copy.deepcopy(self.a);a['clauses']+= [dict(a['clauses'][0],role='effects',polarity=-1)];cs=clauses(a,'a'*64);q=self.q+[dict(self.q[0],evidence_id='q2',role='effects')];sim={(v['evidence_id'],c['clause_id']):.6 for v in q for c in cs if v['role']==c['role']};self.assertEqual(self.run_case(q=q,cs=cs,sim=sim),self.run_case(q=q[::-1],cs=cs[::-1],sim=sim))
 def test_all4081_rivals_unknown(self):
  ids=[str(i)for i in range(4081)];r=aggregate(ids,[.5]*4081,{},[],{});self.assertEqual([x['problem_id']for x in r['rows']],ids)
 def test_bad_population_and_nonfinite(self):
  with self.assertRaises(ValueError):aggregate(['a'],[.5],{},[],{})
  with self.assertRaises(ValueError):aggregate(['a'],[float('nan')],{},[],{},1)
 def test_preopen_gate_and_tamper(self):
  with tempfile.TemporaryDirectory()as td:
   p=pathlib.Path(td)/'authority.json';p.write_text(json.dumps(self.a));events=[]
   def gate(pid):events.append(pid);raise PermissionError('synthetic denial')
   with self.assertRaises(PermissionError):load_authority(p,'0'*64,'p1',gate)
   self.assertEqual(events,['p1'])
   with self.assertRaises(ValueError):load_authority(p,'0'*64,'p1',lambda pid:None)
 def test_bounded_nofollow_reader(self):
  import os
  with tempfile.TemporaryDirectory()as td:
   p=pathlib.Path(td);target=p/'real.json';target.write_text(json.dumps(self.a));h=hashlib.sha256(target.read_bytes()).hexdigest();(p/'link').symlink_to(target);os.mkfifo(p/'fifo')
   for name in ('link','fifo'):
    with self.assertRaises((OSError,ValueError)):load_authority(p/name,h,'p1',lambda pid:None)
   with self.assertRaises(ValueError):load_authority(target,h,'p1',lambda pid:None,maximum_bytes=4)
 def test_dynamic_import_ignores_generic_collision(self):
  import importlib.util,sys,types
  previous=sys.modules.get('representation');sys.modules['representation']=types.SimpleNamespace(ROLES={'WRONG'})
  try:
   spec=importlib.util.spec_from_file_location('service_unique_aggregate',pathlib.Path(__file__).with_name('aggregate.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);self.assertIn('effects',m.ROLES)
  finally:
   if previous is None:sys.modules.pop('representation',None)
   else:sys.modules['representation']=previous
 def test_two_required_constraints_same_role(self):
  a=copy.deepcopy(self.a);a['clauses'].append(dict(a['clauses'][0],span=[10,15]));cs=clauses(a,'a'*64);r=self.run_case(cs=cs)['rows'][0];self.assertEqual(len(r['required_clause_ids']),2);self.assertEqual(len(r['observed_required_clause_ids']),1);self.assertEqual(len(r['unknown_required_clause_ids']),1)
 def test_conflicting_clause_identity_rejected(self):
  other=dict(self.c[0],polarity=-1)
  with self.assertRaises(ValueError):self.run_case(cs=self.c+[other])
 def test_span_invalid(self):
  a=copy.deepcopy(self.a);a['clauses'][0]['span']=[0,100]
  with self.assertRaises(ValueError):clauses(a,'a'*64)
if __name__=='__main__':unittest.main()
