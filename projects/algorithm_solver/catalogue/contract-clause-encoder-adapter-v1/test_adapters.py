import hashlib,json,pathlib,tempfile,unittest
from packets import canonical,sha,load_packets,clause_records,revision,artifact_context
from encoder_binding import BoundEncoder,PROMPT_SHA256,clause_inputs
IDENTITY=dict(encoder_manifest_sha256='a'*64,cpu_manifest_sha256='b'*64,native_python_sha256='c'*64)
class Fake:
 def __init__(self):self.__dict__.update(IDENTITY);self.truncated=False;self.dimension=1024;self.calls=0
 def encode(self,texts,query):
  self.calls+=1;self.last_request_info=dict(rows=len(texts),query=query,truncated=[self.truncated]*len(texts));return [[1.]+[0.]*(self.dimension-1)for _ in texts]
class Tests(unittest.TestCase):
 def packet(self,pid='leetcode:1'):
  c=dict(problem_id=pid,statement_sha256='d'*64,authority_evidence_sha256=['e'*64],domain='Distinct integers.',result={'objective':'Return an input index.'},local_effects={'policy':'Do not mutate inputs.'});return dict(problem_id=pid,contract=c,contract_sha256=sha(canonical(c)),catalogue_problem_contract_sha256='f'*64)
 def test_exact_clause_fields(self):
  p=self.packet();rows=clause_records(p);self.assertEqual(len(rows),3)
  for r in rows:self.assertEqual(r['span'],[0,len(r['text'])]);self.assertEqual(r['authority_sha256'],p['contract_sha256'])
 def test_no_authority_no_invented_clauses(self):
  p=self.packet();p['contract']={'problem_id':p['problem_id']};self.assertEqual(clause_records(p),[])
 def test_finite_scope_retained_without_promotion(self):
  p=self.packet();p['contract']['result']['finite_evidence_scope']='Synthetic finite fixture scope only';p['qualification_scope']={'javascript':{'contract_scope':'finite only','caveats':['synthetic']},'python':{'contract_scope':'finite only','caveats':['synthetic']}};c=artifact_context(p);self.assertEqual(c['qualification_scope'],p['qualification_scope']);self.assertEqual(c['finite_evidence_scope'],'Synthetic finite fixture scope only');self.assertEqual(c['artifact_applicability'],'UNASSESSED');self.assertFalse(c['semantic_similarity_grants_delivery'])
 def test_full_revision_not_filter(self):
  ids=['leetcode:'+str(i)for i in range(1,4082)];record,h=revision(ids,'a'*64,'b'*64,clause_records(self.packet()),'c'*64);self.assertEqual(record['stable_ids'],ids);self.assertFalse(record['artifact_applicability_granted']);self.assertEqual(len(h),64)
 def test_gate_all_before_payload_then_each(self):
  with tempfile.TemporaryDirectory()as td:
   root=pathlib.Path(td)
   def write(n,v):
    p=root/n;p.write_text(json.dumps(v));return dict(path=str(p),sha256=sha(p.read_bytes()))
   rows=[self.packet('leetcode:'+str(i))for i in range(1,25)];ids=[r['problem_id']for r in rows];ps=write('packets.json',rows);cfg=write('gate.json',{});ss=write('selection.json',dict(selected_problem_ids=ids,gate_config_path=cfg['path'],gate_config_sha256=cfg['sha256']));identities=[dict(problem_id=r['problem_id'],reviewed_contract_sha256=r['contract_sha256'],statement_sha256=r['contract']['statement_sha256'],authority_evidence_sha256=r['contract']['authority_evidence_sha256'],catalogue_problem_contract_sha256=r['catalogue_problem_contract_sha256'])for r in rows];ms=write('manifest.json',dict(selection_freeze_sha256=ss['sha256'],private_artifacts={'authority-contract-packets.json':ps['sha256']},selected_problem_ids=ids,contract_identities=identities));events=[];result=load_packets(ss,ms,ps,gate=events.append);self.assertEqual(len(result),24);self.assertEqual(events,ids+ids)
   def deny(pid):raise PermissionError('synthetic gate denial')
   bad=dict(ps,path=str(root/'missing-payload'))
   with self.assertRaises(PermissionError):load_packets(ss,ms,bad,gate=deny)
   rows[0]['contract']['result']['objective']='tampered';bad=write('bad.json',rows)
   with self.assertRaises(ValueError):load_packets(ss,ms,bad,gate=events.append)
 def test_fake_request_exact_binding(self):
  text='Return an integer.';h=sha(text.encode());s=dict(evidence_id='s',request_sha256=h,span=[0,len(text)],text=text,text_sha256=h);e=BoundEncoder(Fake(),IDENTITY,PROMPT_SHA256);r=e.request(text,[s],h);self.assertEqual(len(r),2);self.assertTrue(all(x['request_sha256']==h for x in r));self.assertEqual(e.calls,1)
 def test_request_mismatch_before_encoder(self):
  f=Fake();e=BoundEncoder(f,IDENTITY,PROMPT_SHA256)
  with self.assertRaises(ValueError):e.request('actual',[],'0'*64)
  self.assertEqual(f.calls,0)
 def test_dimension_truncation_and_prompt(self):
  for kind in ('dimension','truncated'):
   f=Fake();setattr(f,kind,2 if kind=='dimension'else True);e=BoundEncoder(f,IDENTITY,PROMPT_SHA256)
   with self.assertRaises(ValueError):e.request('actual',[],sha(b'actual'))
  with self.assertRaises(ValueError):BoundEncoder(Fake(),IDENTITY,'0'*64)
 def test_encoder_identity_mismatch(self):
  with self.assertRaises(ValueError):BoundEncoder(Fake(),dict(IDENTITY,cpu_manifest_sha256='0'*64),PROMPT_SHA256)
 def test_importable_prepare_collision_and_pin_failure(self):
  import importlib.util,sys,types
  path=pathlib.Path(__file__).with_name('prepare.py');spec=importlib.util.spec_from_file_location('private_service_prepare',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  old=sys.modules.get('packets');sys.modules['packets']=types.SimpleNamespace(BAD=True)
  try:self.assertTrue(callable(m.sibling('packets').load_packets))
  finally:
   if old is None:sys.modules.pop('packets',None)
   else:sys.modules['packets']=old
  with tempfile.TemporaryDirectory()as td:
   p=pathlib.Path(td)/'freeze.json';p.write_text(json.dumps({'files':{'packets.py':'0'*64},'dependency_code_sha256':{}}))
   with self.assertRaises(ValueError):m.verify_freeze(dict(path=str(p),sha256=sha(p.read_bytes())))
 def test_clause_prompt_provenance(self):
  rows=clause_records(self.packet());inputs=clause_inputs(rows);self.assertEqual(len(inputs),3);self.assertTrue(all(r['prompt_sha256']==PROMPT_SHA256 and not r['query']for r in inputs));self.assertEqual(len(BoundEncoder(Fake(),IDENTITY,PROMPT_SHA256).encode_records(inputs,False)),3)
if __name__=='__main__':unittest.main()
