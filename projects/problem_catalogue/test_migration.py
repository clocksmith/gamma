import copy,hashlib,importlib.util,json,os
from pathlib import Path
import subprocess,sys,tempfile,unittest
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
import migrate as M
import embeddings as E
from schema import SCHEMA,generate
from jsonschema import Draft202012Validator

class MigrationTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.roots={}
  for name in ('gamma','simulatte','hatch'):
   p=self.root/name;p.mkdir();(p/'AGENTS.md').write_text('Synthetic test fixture.');subprocess.run(['git','init','-q',str(p)],check=True);subprocess.run(['git','-C',str(p),'add','AGENTS.md'],check=True);subprocess.run(['git','-C',str(p),'-c','user.email=test@example.test','-c','user.name=Fixture','commit','-qm','Fixture'],check=True);self.roots[name]=p
  self.args=SimpleNamespace(**{k:str(v) for k,v in self.roots.items()},gamma_catalogue=None,mesh_session=None,encoder_contract=None,embedding_baseline=None);self.run=M.Run(self.root/'destination')
 def tearDown(self):self.temp.cleanup()
 def fixture(self,extra=False):
  path=self.roots['gamma']/'projects/question_bank/hack2hire';path.mkdir(parents=True,exist_ok=True)
  rows=[{'uid':'hack2hire:one','source_post_id':'one','title':'Identical title','category':'coding','companies':['Example Co'],'topics':[],'variants':[{'id':'a','ordinal':1},{'id':'b','ordinal':2}],'url':'https://example.test/one','leetcode_overlap':{'candidates':[]}}]
  if extra:rows.insert(0,{'uid':'hack2hire:two','source_post_id':'two','title':'Identical title','category':'coding','companies':[],'variants':[],'url':'https://example.test/two'})
  (path/'bank.json').write_text(json.dumps({'records':rows}));(path/'descriptions.json').write_text(json.dumps({'records':[{'source_post_id':'one','description':{'excerpt':'A public preview'},'source_last_report_seen':None}]}));return path/'bank.json'
 def through_convert(self):
  for fn in (M.inventory,M.extract,M.resolve,M.convert):fn(self.run,self.args)
  return M.load_records(self.run)
 def test_partial_variants_title_collisions_and_immutable_idempotence(self):
  self.fixture();first=self.through_convert();M.validate(self.run,self.args)
  contracts=[v for (k,_),(_,v) in first.items() if k=='contract'];self.assertEqual(len(contracts),2);self.assertTrue(all(c['contentScope']=='preview' and c['requirements']['status']=='missing' for c in contracts));self.assertEqual(len([k for k in first if k[0]=='company-report']),2)
  second=self.through_convert();self.assertEqual({k:r['sha256'] for k,(r,v) in first.items()},{k:r['sha256'] for k,(r,v) in second.items()})
  self.fixture(extra=True);third=self.through_convert();self.assertEqual(len([k for k in third if k[0]=='problem']),2,'same title cannot merge source identities')
  for key,(ref,value) in first.items():self.assertEqual(third[key][0],ref,'newly arriving rows must not re-version unchanged records, even after insertion')
 def test_changed_content_versions_without_overwriting_previous_files(self):
  path=self.fixture();first=self.through_convert();key=('problem','hack2hire:one');oldref=first[key][0];oldbytes=(self.run.dest/oldref['path']).read_bytes();data=json.loads(path.read_text());data['records'][0]['title']='New title';path.write_text(json.dumps(data));second=self.through_convert();self.assertGreater(second[key][0]['version'],oldref['version']);self.assertEqual((self.run.dest/oldref['path']).read_bytes(),oldbytes)
 def test_source_inventory_never_opens_candidate_payload_and_never_guesses_identity(self):
  p=self.roots['gamma']/'projects/algorithm_solver/catalogue/authored/fixture/python/42.py';p.parent.mkdir(parents=True);p.write_text('raise RuntimeError("MUST NOT RUN OR READ")')
  original=Path.read_bytes
  def guarded(path):
   if path==p:raise AssertionError('Candidate payload opened')
   return original(path)
  with patch.object(Path,'read_bytes',guarded):records=self.through_convert()
  problem=[v for (kind,_),(r,v) in records.items() if kind=='problem'][0];self.assertEqual(problem['identity']['status'],'unresolved');self.assertNotEqual(problem['id'],'leetcode:42')
 def test_hash_tampering_and_reference_escape_fail_closed(self):
  self.fixture();self.through_convert();r=self.run.phase('convert')['records'][0];p=self.run.dest/r['path'];p.write_bytes(p.read_bytes()+b' ')
  with self.assertRaisesRegex(ValueError,'hash mismatch'):M.load_records(self.run)
  with self.assertRaises(ValueError):M.within(self.run.dest,self.root/'outside')
 def test_hex_variant_sources_and_assignment_metadata_are_preserved_without_admission(self):
  root=self.roots['gamma'];authored=root/'projects/algorithm_solver/catalogue/authored';batch=authored/'hack2hire-chunk03-v1';variant='69c87bbe21f6ab4226966de6';paths=[]
  for language,suffix in (('python','py'),('javascript','js')):
   p=batch/language/(variant+'.'+suffix);p.parent.mkdir(parents=True);p.write_text('UNOPENED CANDIDATE');paths.append(p)
  (batch/'semantics.json').write_text('{"status":"unknown"}')
  work=authored/'hack2hire-worklists-fixture/chunk03.txt';work.parent.mkdir();work.write_text('post\tImplement itoa()\t'+variant+'\n')
  original=Path.read_bytes
  def guarded(path):
   if path in paths:raise AssertionError('Candidate source opened')
   return original(path)
  with patch.object(Path,'read_bytes',guarded):records=self.through_convert();M.validate(self.run,self.args)
  self.assertEqual(len([k for k in records if k[0]=='problem']),1)
  self.assertFalse(any(k[0]=='admission' for k in records))
  artifacts=[v for (k,_),(r,v) in records.items() if k=='artifact'];self.assertEqual(len([v for v in artifacts if v['type']=='implementation']),2)
  self.assertEqual(len([v for v in artifacts if v['nativeMetadata']['status']=='present' and v['nativeMetadata']['value'].get('role') in ('hack-worklist','gamma-source-metadata')]),2)
  claims=self.run.phase('resolve-identities')['proposedRelationships'];self.assertTrue(all(c['candidateExternalId']=='hack2hire:'+variant and not c['mergeAllowed'] for c in claims))
 def test_new_assignment_metadata_is_reported_after_snapshot(self):
  self.fixture();self.through_convert();M.validate(self.run,self.args);M.build_catalogue(self.run,self.args);M.build_embeddings(self.run,self.args)
  work=self.roots['gamma']/'projects/algorithm_solver/catalogue/authored/hack2hire-worklists-fixture/chunk18.txt';work.parent.mkdir(parents=True);work.write_text('post\tTitle\tvariant\n');report=M.reconcile(self.run,self.args)
  self.assertTrue(report['snapshotFaithfullyMigrated']);self.assertFalse(report['sourceCaughtUp']);self.assertEqual(report['newGammaMetadataFilesSinceSnapshot'],[str(work.relative_to(self.roots['gamma']))])
 def authored_record_fixture(self):
  self.fixture();existing=self.through_convert();contract=copy.deepcopy(next(v for (k,_),(r,v) in existing.items() if k=='contract'));root=self.roots['gamma'];batch=root/'projects/algorithm_solver/catalogue/authored/hack2hire-chunk03-v1';records=batch/'study-records';records.mkdir(parents=True)
  source=batch/'python/42.py';source.parent.mkdir();source.write_text('DO NOT OPEN THIS CANDIDATE');ptr=contract['origin'][0];pid='leetcode:42';aid='approach:leetcode:42:authored-v1';contract.update(id='contract:leetcode:42:authored-v1',problemId=pid,contentScope='authored',native=[],sources=[]);contract['assumptions']=M.present([{'spec_basis':'inferred','who':'fixture','basis':'public preview'}],ptr)
  def save(name,value):
   p=records/name;p.write_bytes(M.encoded(value));return {'kind':value['kind'],'id':value['id'],'version':value['version'],'path':str(p.relative_to(root)),'sha256':M.sha(p.read_bytes())}
  cr=save('contract.json',contract)
  implementation={'schema':'study.record.v1','kind':'artifact','id':'artifact:leetcode:42:python:v1','version':1,'origin':[ptr],'type':'implementation','title':'Fixture implementation','problemId':pid,'approachId':aid,'contract':cr,'file':M.present({'path':str(source.relative_to(root)),'sha256':M.sha(source.read_bytes()),'bytes':source.stat().st_size,'mediaType':'text/x-python'},ptr),'externalLocator':M.na('File is in cohort'),'language':'python','documentSchema':None,'executionKind':'code','complexityClaims':M.missing('No claim'),'nativeMetadata':M.missing('No metadata')};ir=save('implementation.json',implementation)
  stages=[]
  for name in ('reasoning','coding','validation'):
   stages.append({'id':name,'type':name,'title':M.present(name,ptr),'question':M.present('What must hold?',ptr),'explanation':M.present('Authored explanation',ptr),'rationale':M.present('Authored rationale',ptr),'instructions':M.present([],ptr),'observations':M.missing('Not supplied'),'hints':M.present(['First reason about the invariant'],ptr),'requirementIds':M.missing('Not supplied'),'checks':[],'artifacts':[ir] if name=='coding' else [],'native':ir})
  approach={'schema':'study.record.v1','kind':'approach','id':aid,'version':1,'origin':[ptr],'problemId':pid,'contract':cr,'title':M.present('Authored approach',ptr),'representation':'coding','explanation':M.present('Authored explanation',ptr),'chooseWhen':M.present([],ptr),'tradeoffs':M.present([],ptr),'invariants':M.present(['Preserve values'],ptr),'hints':M.present(['First hint','Second hint'],ptr),'stages':stages,'sequenceStatus':'draft','native':ir};ar=save('approach.json',approach)
  return root,source,cr,ir,ar
 def test_authored_records_rebase_pinned_dependencies_and_leave_code_unopened(self):
  root,source,cr,ir,ar=self.authored_record_fixture();original=Path.read_bytes
  def guarded(path):
   if path==source:raise AssertionError('Authored code opened')
   return original(path)
  with patch.object(Path,'read_bytes',guarded):records=self.through_convert();M.validate(self.run,self.args)
  implementation=records['artifact',ir['id']][1];approach=records['approach',ar['id']][1];contract=records['contract',cr['id']][1]
  self.assertEqual(implementation['file']['status'],'missing');self.assertEqual(implementation['externalLocator']['value']['sha256'],M.sha(b'DO NOT OPEN THIS CANDIDATE'))
  self.assertTrue(implementation['contract']['path'].startswith('records/contract/'));self.assertEqual(approach['hints']['value'],['First hint','Second hint']);self.assertEqual(contract['assumptions']['value'][0]['spec_basis'],'inferred');self.assertEqual([s['type'] for s in approach['stages']],['reasoning','coding','validation']);self.assertEqual(self.run.phase('resolve-identities')['studySourcePaths'][str(source.relative_to(root))],'leetcode:42')
  second=self.through_convert();self.assertEqual(records['approach',ar['id']][0],second['approach',ar['id']][0]);self.assertFalse(any(k=='admission' for k,_ in records))
 def test_unfinished_authored_dependencies_are_blocked_without_discarding_native_records(self):
  root,source,cr,ir,ar=self.authored_record_fixture();p=root/ar['path'];value=M.read(p);value['contract']['sha256']='f'*64;p.write_bytes(M.encoded(value));records=self.through_convert();self.assertNotIn(('approach',ar['id']),records)
  blocked=[r for r in self.run.phase('convert')['rows'] if r['status']=='blocked'];self.assertTrue(any('mismatch' in r['reason'] for r in blocked));self.assertIn(('artifact','input:gamma:'+ar['path']),records)
 def test_present_empty_is_different_from_absent_or_unknown(self):
  pointer={'repository':'fixture','revision':None,'path':'x.json','sha256':'a'*64,'selector':''};f=M.field({'items':[]},'items',pointer);self.assertEqual(f['status'],'present');self.assertEqual(f['value'],[]);self.assertEqual(M.field({},'items',pointer)['status'],'missing');validator=Draft202012Validator({**SCHEMA,'oneOf':[{'$ref':'#/$defs/ListField'}]});validator.validate(f)
  with self.assertRaises(Exception):validator.validate({'status':'unknown'})
 def test_live_changes_and_new_sources_are_reported_not_absorbed(self):
  path=self.fixture();self.through_convert();M.validate(self.run,self.args);M.build_catalogue(self.run,self.args);M.build_embeddings(self.run,self.args);path.write_text(path.read_text()+' ');p=self.roots['gamma']/'projects/algorithm_solver/catalogue/authored/new/python/99.py';p.parent.mkdir(parents=True);p.write_text('pass');report=M.reconcile(self.run,self.args);self.assertTrue(report['snapshotFaithfullyMigrated']);self.assertFalse(report['sourceCaughtUp']);self.assertEqual(len(report['changedSinceSnapshot']),1);self.assertEqual(len(report['newGammaSourceFilesSinceSnapshot']),1)
 def test_upstream_changes_invalidate_downstream_phases(self):
  path=self.fixture();self.through_convert();data=json.loads(path.read_text());data['records'][0]['title']='Changed';path.write_text(json.dumps(data));M.inventory(self.run,self.args)
  with self.assertRaisesRegex(ValueError,'Stale'):M.convert(self.run,self.args)
 def test_native_provenance_changes_are_not_dropped_as_migration_metadata(self):
  ptr={'repository':'fixture','revision':None,'path':'x.json','sha256':'a'*64,'selector':''};w=M.Writer(self.run);w.artifact('artifact:one',ptr,metadata={'provenance':{'source':'one'}})
  with self.assertRaisesRegex(ValueError,'Conflicting'):w.artifact('artifact:one',ptr,metadata={'provenance':{'source':'two'}})
 def test_original_source_snapshot_tampering_is_detected(self):
  self.fixture();self.through_convert();item=next(x for x in self.run.phase('inventory')['items'] if x['role']=='hack-bank');path=self.run.dest/item['snapshot'];path.write_bytes(path.read_bytes()+b' ')
  with self.assertRaises(ValueError):M.validate(self.run,self.args)
 def test_historical_catalogue_reference_is_not_a_new_admission(self):
  p=self.root/'historical.json';p.write_text(json.dumps({'schema':'gamma.dual-language-catalogue.v2','problems':[{'problem_id':'leetcode:42','implementations':{'python':{'status':'qualified','source_sha256':'a'*64,'canonical_variant_id':'python:old','provenance':{'source':'historical'}},'javascript':{'status':'blocked','reason':'unknown'}}}]}));self.args.gamma_catalogue=str(p);records=self.through_convert();evidence=[v for (k,_),(r,v) in records.items() if k=='evidence'];self.assertEqual(evidence[0]['bindingStatus'],'unbound');self.assertEqual(evidence[0]['admissionEffect'],'none');self.assertEqual(len(evidence[0]['subjects']),1);self.assertFalse(any(k=='admission' for k,_ in records))
 def test_duplicate_or_nonfinite_json_and_duplicate_source_records_are_rejected(self):
  with self.assertRaises(ValueError):M.decode('{"x": 1, "x": 2}')
  with self.assertRaises(ValueError):M.decode('{"x": NaN}')
  path=self.fixture();data=json.loads(path.read_text());data['records'].append(data['records'][0]);path.write_text(json.dumps(data));M.inventory(self.run,self.args)
  with self.assertRaisesRegex(ValueError,'Duplicate source'):M.extract(self.run,self.args)
 def test_generated_contracts_do_not_drift(self):
  output=self.root/'generated';output.mkdir();generate(output)
  for name in ('schema.v1.ts','schema.v1.json'):self.assertEqual((output/name).read_bytes(),(Path(__file__).parent/name).read_bytes())

class EmbeddingTests(unittest.TestCase):
 def test_exact_reuse_purpose_separation_and_changed_text(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);encoder=root/'fixture.py';counter=root/'counter';encoder.write_text('import sys,json,pathlib\np=pathlib.Path(sys.argv[1]);p.write_text(str(int(p.read_text())+1) if p.exists() else "1")\nr=json.load(sys.stdin);print(json.dumps({"encoderIdentity":r["encoderIdentity"],"vectors":[{"id":x["id"],"textSha256":x["textSha256"],"values":[len(x["text"]),1,2,3]} for x in r["inputs"]]}))\n')
   identity={k:hashlib.sha256(k.encode()).hexdigest() if k.endswith('Sha256') else {'modelId':'synthetic-test-fixture','modelRevision':'v1','maxTokens':64,'normalization':'none','pooling':'fixture','dtype':'float32','documentInstruction':'fixture','queryInstruction':'fixture','truncation':'none'}[k] for k in E.IDENTITY};contract={'schema':'study.encoder-contract.v1','command':[sys.executable,str(encoder),str(counter)],'commandFile':str(encoder),'commandFileSha256':E.sha(encoder.read_bytes()),'encoderIdentity':identity,'recipe':{'chunker':'codepoint-window-v1','maxCharacters':1200,'overlapCharacters':100},'dimensions':4};cp=root/'encoder.json';cp.write_text(json.dumps(contract))
   ref={'kind':'contract','id':'fixture:one','version':1,'path':'records/contract/x/v1.json','sha256':'a'*64};rows=[{'id':'first','purpose':'problem-discovery','owner':ref,'field':'statement','chunkOrdinal':0,'text':'abc','textSha256':E.sha(b'abc')},{'id':'second','purpose':'solution-study','owner':ref,'field':'explanation','chunkOrdinal':0,'text':'abc','textSha256':E.sha(b'abc')}]
   first=E.build(root/'first',rows,cp);self.assertEqual(first['newVectors'],2);baseline=root/'first/generated/embeddings/release.json';modified=copy.deepcopy(rows);modified[0]['owner']['version']=2;second=E.build(root/'second',modified,cp,baseline);self.assertEqual(second['newVectors'],0);self.assertEqual(second['reusedVectors'],2);self.assertEqual(counter.read_text(),'1')
   modified[0]['text']='changed';modified[0]['textSha256']=E.sha(b'changed');third=E.build(root/'third',modified,cp,baseline);self.assertEqual(third['newVectors'],1);self.assertEqual(counter.read_text(),'2')
   contract['encoderIdentity']['pooling']='different';cp.write_text(json.dumps(contract));fourth=E.build(root/'fourth',rows,cp,baseline);self.assertEqual(fourth['newVectors'],2)
 def test_missing_encoder_produces_a_plan_not_fake_vectors(self):
  with tempfile.TemporaryDirectory() as td:
   result=E.build(Path(td),[],None);self.assertEqual(result['status'],'blocked-missing-encoder-identity');self.assertFalse((Path(td)/'generated/embeddings/release.json').exists())

if __name__=='__main__':unittest.main()
