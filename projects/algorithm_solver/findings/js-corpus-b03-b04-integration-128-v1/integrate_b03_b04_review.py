"""Integrate only the coordinator-authorized33 plus separately reviewed115."""
from pathlib import Path
import copy,hashlib,json,subprocess,sys
REPO=Path('/home/x/deco/gamma');ROOT=REPO/'projects/algorithm_solver';TASK=Path('/home/x/Documents/Codex/2026-10-19/task');PACK=TASK/'js-corpus-wave-001'
FIND=ROOT/'findings/js-corpus-b03-b04-integration-128-v1';RUN=ROOT/'runs/js-corpus-contract-review-128-v1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def rel(p):
 p=Path(p);return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)
def copy_source(source,dest):
 if dest.exists():assert dest.read_bytes()==source.read_bytes(),('Conflicting destination',str(dest))
 else:
  with dest.open('xb') as f:f.write(source.read_bytes())
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()=='dfbb344e457e4427c2233593bc3334b7951f422d'
oldpath=ROOT/'findings/js-corpus-b05-integration-128-v1/catalog.json';old=json.loads(oldpath.read_text());assert old['unique_problems']==24 and old['independent_cases']==2217
oldhash=sha(oldpath);serving=ROOT/'runs/known-sortedcontainers-catalog-128-v1/approved-library.json';serving_hash=sha(serving)
manifest=json.loads((PACK/'manifest.json').read_text());byid={r['id']:r for r in manifest['rows']}
review=json.loads((RUN/'review-summary.json').read_text());assert review['review115']['accepted']
candidate_review=json.loads((TASK/'b03-b04-review-summary.json').read_text());assert candidate_review['qualified']==33 and candidate_review['qualified_independent_cases']==2777
sources=[]
for row in old['rows']:
 assert sha(ROOT/row['source'])==row['source_sha256']
 sources.append(copy.deepcopy(row))
for batch in candidate_review['batches']:
 for item in batch['rows']:
  if not item['qualified']:continue
  n=item['id'];source=REPO/item['selected_source'];receipt=REPO/item['selected_receipt'];r=json.loads(receipt.read_text());row=byid[n]
  assert sha(source)==item['source_sha256'] and sha(receipt)==item['selected_receipt_sha256']
  assert r['qualified'] and r['independent_passed']==item['independent_total']
  assert all(x['python']['passed'] and x['javascript']['passed'] for x in r['results'])
  b=ROOT/'runs/js-corpus-wave-001'/batch['batch'];diff=b/f'{n:04d}-style-differential.json';d=json.loads(diff.read_text());assert d['all_original_outcomes_preserved'] and d['runtime_results_mutation_and_aliasing_match']
  seal=b/'original-source-seal.json';sem=receipt.parent/'semantics.json'
  sources.append(dict(id=n,key=item['key'],origin=batch['batch'],source_input=rel(source),source_sha256=sha(source),independent_cases=item['independent_total'],qualification_receipt=rel(receipt),qualification_receipt_sha256=sha(receipt),semantics=rel(sem),semantics_sha256=sha(sem),normalization_receipt=rel(b/f'{n:04d}-normalization.json'),normalization_receipt_sha256=sha(b/f'{n:04d}-normalization.json'),style_differential_receipt=rel(diff),style_differential_receipt_sha256=sha(diff),style_differential_applies_to_selected=n not in [62,69],source_provenance=dict(kind='owner-supplied-agent-candidate',original_source_seal=rel(seal),original_source_seal_sha256=sha(seal),reference_attribution='Pinned local reference reviewed for behavior; not claimed as the origin of the owner candidate.'),numeric_successor=n in [62,69],semantic_scope=['Finite development qualification, not formal correctness or maximum-bound performance.','Raw sources and tests remain private; public and independent expectations were not rewritten.']))
source=ROOT/'runs/js-exact-integer-115-128-v1/candidate.js';receipt=ROOT/'runs/js-exact-integer-115-128-v1/summary.json';row=byid[115]
sources.append(dict(id=115,key=row['key'],origin='W001-B05-exact-integer-successor',source_input=rel(source),source_sha256=sha(source),independent_cases=101,qualification_receipt=rel(receipt),qualification_receipt_sha256=sha(receipt),contract_review=rel(RUN/'115-contract-review.json'),contract_review_sha256=sha(RUN/'115-contract-review.json'),semantics='runs/js-corpus-wave-001/W001-B05/0115/attempt-002/semantics.json',semantics_sha256=sha(ROOT/'runs/js-corpus-wave-001/W001-B05/0115/attempt-002/semantics.json'),source_provenance=row['local_sources'],numeric_successor=True,semantic_scope=['Native BigInt count recurrence and exact tagged transport required for large counts.','Finite ASCII-string development qualification; no new autonomous solve.']))
assert len(sources)==len({r['id'] for r in sources})==len({r['key'] for r in sources})==58
assert sum(r['independent_cases'] for r in sources)==5095
data=ROOT/'data/derived/bilingual_development_corpus_v2';(data/'javascript').mkdir(parents=True,exist_ok=True);(data/'python').mkdir(exist_ok=True)
foundation=json.loads((ROOT/'findings/source-corpus-js-py-128-v3/qualified-catalog.json').read_text())
foundation={r['key']:r for r in foundation['catalog']};rows=[]
for row in sorted(sources,key=lambda r:r['id']):
 n=row['id'];jsp=ROOT/row['source_input'];assert sha(jsp)==row['source_sha256']
 jsdest=data/'javascript'/f'{n:04d}.js';copy_source(jsp,jsdest);row['source']=rel(jsdest);row['language']='javascript';row['qualification']='public-and-existing-independent-tests-passed; development only'
 if n in byid:
  assignment=byid[n];pyp=Path(assignment['python_source']);assert sha(pyp)==assignment['python_source_sha256']
  packet=json.loads(Path(assignment['problem_packet']).read_text())
  py=dict(language='python',source_input=rel(pyp),source_sha256=sha(pyp),normalization='Original independently tested approved Python source retained; not forced into the JavaScript algorithm or naming style.',qualification_receipt=row['qualification_receipt'],qualification_receipt_sha256=row.get('qualification_receipt_sha256'),independent_cases=row['independent_cases'],qualified=True,provenance=dict(assignment_manifest_sha256=sha(PACK/'manifest.json'),problem_packet_sha256=assignment['problem_packet_sha256'],license=packet['license'],attribution=packet['attribution']))
  if n in [62,69]:py['qualification_receipt_note']='Python was rerun with unchanged mathematical expectations in the separately sealed numeric successor receipt.'
 else:
  original=foundation[row['key']];impl=next(i for i in original['implementations'] if i['language']=='python');assert impl['qualified'] and impl['tests']['public']['passed'] and impl['tests']['independent']['passed']
  pyp=ROOT/impl['source']['path'];assert sha(pyp)==impl['source']['sha256']
  py=dict(language='python',source_input=rel(pyp),source_sha256=sha(pyp),normalization='Preserved qualified five-family Python normalization.',qualification_receipt='findings/source-corpus-js-py-128-v3/qualified-catalog.json',qualification_receipt_sha256=sha(ROOT/'findings/source-corpus-js-py-128-v3/qualified-catalog.json'),independent_cases=impl['tests']['independent']['tests_total'],qualified=True,provenance=dict(source_seal_sha256=original['source_seal_sha256'],evidence_run=original['evidence_run']))
  assert py['independent_cases']==row['independent_cases']
 pydest=data/'python'/f'{n:04d}.py';copy_source(pyp,pydest);py['source']=rel(pydest)
 js=copy.deepcopy(row);js.pop('id');js.pop('key');js['qualified']=True
 rows.append(dict(id=n,key=row['key'],independent_cases=row['independent_cases'],implementations=[js,py]))
catalog=dict(schema='algsolve.bilingual-development-corpus.v2',scope='Private language-specific development corpus for semantic macro discovery; production recognition and composer unchanged.',unique_problems=58,implementations=116,language_implementations={'javascript':58,'python':58},independent_cases_per_language=5095,paired_independent_execution_count=10190,unique_before=24,added_b03_b04_unique=33,added_115_unique=1,duplicate_ids=0,duplicate_keys=0,excluded_unqualified_ids=[60,65,74,78,81,87,90],separately_corrected_pending_integration_ids=[78,90],no_new_owner_batches=["W001-B01","W001-B02"],autonomous_new_solves=0,source_policy='Raw source bodies and tests remain ignored/private; tracked catalog contains hashes, provenance, normalization and receipts only.',rows=rows)
write(FIND/'catalog.json',catalog);write(ROOT/'data/derived/bilingual_development_catalog_v2.json',catalog)
js_catalog=dict(schema='algsolve.javascript-development-corpus.v2',scope=catalog['scope'],unique_problems=58,implementations=58,independent_cases=5095,rows=[dict(id=r['id'],key=r['key'],**r['implementations'][0]) for r in rows])
write(ROOT/'data/derived/javascript_development_catalog_v2.json',js_catalog)
record=dict(schema='algsolve.b03-b04-coordinator-integration.v1',base_commit='dfbb344e457e4427c2233593bc3334b7951f422d',scope='Coordinator review and integration of33 passing B03/B04 candidates plus115 after exact-integer review.78/90 correction results remain separately reviewable, not silently added.',reviewer='Primary128 task; no claim of independent human or second-agent review.',prior_catalog_sha256=oldhash,candidate_review_sha256=sha(TASK/'b03-b04-review-summary.json'),contract_review_sha256=sha(RUN/'review-summary.json'),review115_sha256=sha(RUN/'115-contract-review.json'),catalog_sha256=sha(FIND/'catalog.json'),unique_before=24,added_unique=34,unique_after=58,implementations=116,independent_cases_per_language=5095,duplicate_ids=0,duplicate_keys=0,protected_opened=False,production_catalog_sha256=serving_hash,production_catalog_unchanged=sha(serving)==serving_hash,old_catalog_unchanged=sha(oldpath)==oldhash,public_push=False,public_deployment=False)
write(FIND/'integration.json',record)
assert record['production_catalog_unchanged'] and record['old_catalog_unchanged']
for r in rows:
 for impl in r['implementations']:
  p=ROOT/impl['source'];assert sha(p)==impl['source_sha256']
  assert subprocess.run(['git','check-ignore',str(p)],cwd=REPO,stdout=subprocess.DEVNULL).returncode==0
print(json.dumps(record,indent=2))
