"""Synthetic contracts/metadata only. No candidates, models or sealed cohorts."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from . import recognition_documents as r
from .test_boundary_policy import BoundaryPolicyTests

class Documents(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  raw,pins=BoundaryPolicyTests().fixture();paths={}
  for name,data in raw.items():
   p=self.root/(name+'.json');p.write_bytes(data);paths[name]=str(p)
  self.gate={'schema':'gamma.boundary-gate-config.v1','artifact_paths':paths,'trusted_hashes':pins}
  self.plan={'schema':'gamma.recognition-document-plan.v1','title_metadata':self.write('titles',{'rows':[{'global_problem_id':f'leetcode:{i}','title':f'Synthetic title {i}','source_availability':'unverified'}for i in range(1,6)]}),
   'boundary_gate':self.write('gate',self.gate),'authority_roots':[str(self.root)],'expected_population':5,'authorities':[]}
 def write(self,name,value):
  p=self.root/(name+'.json');p.write_bytes(r.encoded(value));return {'path':str(p),'sha256':r.sha(p.read_bytes())}
 def authority(self,pid='leetcode:1'):
  freeze=self.write('freeze',{'ids':[int(pid.split(':')[1])]})
  review=self.write('review',{'independent_review':True,'freeze_sha256':freeze['sha256']})
  contract={'problem_id':pid,'numeric_problem_id':int(pid.split(':')[1]),'statement_sha256':'a'*64,
    'result':{'type':'integer','semantics':'Count distinct positive values.'},'domain':{'values':'positive integers'},
    'interface':{'entrypoint':'solve','arguments':'ordered-positional','parameters':[['values','integer[]']]}}
  authority=self.write('authority',{'schema':'gamma.public-batch-authority-review.v1','freeze_sha256':freeze['sha256'],
    'review_sha256':review['sha256'],'review_scope':'independent-statement-identity-domain-interface-effects-complexity',
    'reviewer':'independent synthetic reviewer','source_publication_authorized':False,'contracts':{pid:contract},
    'evidence_artifacts':[{'identity':'synthetic-public-snapshot','sha256':'a'*64,'role':'reviewed-statement-snapshot'}]})
  return {'problem_id':pid,'kind':'reviewed-public-batch','authority':authority,'review':review,'freeze':freeze,'statement_sha256':'a'*64}
 def test_full_index_retained_title_only(self):
  got=r.build(self.plan);self.assertEqual(got['stable_ids'],[f'leetcode:{i}'for i in range(1,6)])
  self.assertEqual(got['title_only'],5);self.assertEqual(got['enriched'],0)
  self.assertTrue(all(d['authority']['knowledge_class']=='title-only'for d in got['documents']))
 def test_deterministic_enrichment_no_status_features(self):
  self.plan['authorities']=[self.authority()];a=r.build(self.plan);b=r.build(self.plan)
  self.assertEqual(a,b);self.assertEqual(a['population'],5);self.assertEqual(a['enriched'],1)
  d=a['documents'][0];self.assertIn('Count distinct',d['text']);self.assertNotIn('qualified',d['text'])
  self.assertEqual(d['document_sha256'],r.sha(d['text'].encode()))
  for later in a['documents'][1:]:self.assertNotIn('Input domain:',later['text'])
 def test_reserved_and_unknown_never_open_authority(self):
  for pid in ('leetcode:3','leetcode:4','leetcode:5'):
   self.plan['authorities']=[self.authority(pid)]
   with patch.object(r,'authority_bytes',side_effect=AssertionError('must not open')):
    with self.assertRaises(PermissionError):r.build(self.plan)
 def test_live_gate_precedes_each_authority_open(self):
  self.plan['authorities']=[self.authority()];events=[];original=r.authority_bytes;gate=r.boundary_policy.authorize_before_open
  def authorize(*a,**k):events.append('gate');return gate(*a,**k)
  def read(*a,**k):self.assertEqual(events[-1],'gate');events.append('read');return original(*a,**k)
  with patch.object(r.boundary_policy,'authorize_before_open',side_effect=authorize),patch.object(r,'authority_bytes',side_effect=read):r.build(self.plan)
  self.assertEqual(events,['gate','read']*3)
 def test_boundary_drift_during_authority_reads(self):
  self.plan['authorities']=[self.authority()];original=r.authority_bytes;calls=[]
  def read(*a,**k):
   data=original(*a,**k);calls.append(1);Path(self.gate['artifact_paths']['policy']).write_text('{}');return data
  with patch.object(r,'authority_bytes',side_effect=read):
   with self.assertRaises(ValueError):r.build(self.plan)
  self.assertEqual(len(calls),1)
 def test_authority_hash_and_review_binding_fail_closed(self):
  row=self.authority();self.plan['authorities']=[row];Path(row['authority']['path']).write_text('{}')
  with self.assertRaises(ValueError):r.build(self.plan)
  row=self.authority();self.plan['authorities']=[row];row['statement_sha256']='b'*64
  with self.assertRaises(ValueError):r.build(self.plan)
 def test_extra_duplicate_or_filtered_identity_rejected(self):
  row=self.authority();self.plan['authorities']=[row,copy.deepcopy(row)]
  with self.assertRaises(ValueError):r.build(self.plan)
  self.plan['authorities']=[];self.plan['expected_population']=4
  with self.assertRaises(ValueError):r.build(self.plan)
 def test_unknown_availability_does_not_change_documents(self):
  a=r.build(self.plan);p=Path(self.plan['title_metadata']['path']);metadata=json.loads(p.read_bytes())
  for row in metadata['rows']:row['source_availability']='definitely-unavailable'
  self.plan['title_metadata']=self.write('titles',metadata);b=r.build(self.plan)
  self.assertEqual([d['text']for d in a['documents']],[d['text']for d in b['documents']])
 def test_artifact_paths_not_followed(self):
  row=self.authority();a=json.loads(Path(row['authority']['path']).read_bytes());a['source_path']='/never/read/submitted.py';row['authority']=self.write('authority',a);self.plan['authorities']=[row]
  got=r.build(self.plan);self.assertNotIn('source_path',got['documents'][0]['text'])
 def test_roots_symlinks_and_traversal_rejected(self):
  row=self.authority();self.plan['authorities']=[row];source=Path(row['authority']['path']);target=self.root/'actual.json';source.rename(target);source.symlink_to(target)
  with self.assertRaises(OSError):r.build(self.plan)
 def test_wrong_global_identity_rejected(self):
  row=self.authority();a=json.loads(Path(row['authority']['path']).read_bytes());a['contracts']['leetcode:1']['numeric_problem_id']=2;row['authority']=self.write('authority',a);self.plan['authorities']=[row]
  with self.assertRaises(ValueError):r.build(self.plan)
 def test_noncanonical_interface_rejected(self):
  row=self.authority();a=json.loads(Path(row['authority']['path']).read_bytes());a['contracts']['leetcode:1']['interface']['entrypoint']='anything';row['authority']=self.write('authority',a);self.plan['authorities']=[row]
  with self.assertRaises(ValueError):r.build(self.plan)

if __name__=='__main__':unittest.main()

class BaselineDelta(Documents):
 def test_unchanged_exact_titlebytes_and_only_one_delta(self):
  baseline={'documents':[{'problem_id':f'leetcode:{i}','text':f'Synthetic title {i}'}for i in range(1,6)]}
  self.plan['baseline_documents']=self.write('baseline',baseline);self.plan['authorities']=[self.authority()]
  result=r.build(self.plan);self.assertEqual(result['changed_problem_ids'],['leetcode:1'])
  self.assertEqual(result['unchanged_problem_ids'],[f'leetcode:{i}'for i in range(2,6)])
  self.assertEqual([d['text']for d in result['documents'][1:]],[d['text']for d in baseline['documents'][1:]])
 def test_prior_index_filter_or_order_change_rejected(self):
  docs=[{'problem_id':f'leetcode:{i}','text':f'Synthetic title {i}'}for i in range(1,6)]
  for altered in (docs[:-1],list(reversed(docs))):
   self.plan['baseline_documents']=self.write('baseline',{'documents':altered})
   with self.assertRaises(ValueError):r.build(self.plan)
 def test_non_title_baseline_semantics_not_imported(self):
  docs=[{'problem_id':f'leetcode:{i}','text':f'Synthetic title {i}'}for i in range(1,6)];docs[0]['text']+=' hidden claim'
  self.plan['baseline_documents']=self.write('baseline',{'documents':docs})
  with self.assertRaises(ValueError):r.build(self.plan)
