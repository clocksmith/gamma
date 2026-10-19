from pathlib import Path
import collections,copy,hashlib,json,subprocess,shutil
REPO=Path('/home/x/deco/gamma');R=REPO/'projects/algorithm_solver';T=Path('/home/x/Documents/Codex/2026-10-19/task');PACK=T/'js-corpus-wave-001';OUT=R/'runs/js-corpus-b01-b02-review-128-v1';FIND=R/'findings/js-corpus-b01-b02-integration-128-v1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rel=lambda p:str(Path(p).relative_to(R))
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()=='2558e83f80c16da33b4dc848af965f04d3b03ce5'
prior=R/'findings/js-corpus-subset-domain-128-v1/catalog.json';old=json.loads(prior.read_text());assert sha(prior)=='1f57fe55767238e6bd8425f28c6a6c5cd1bc886ae3a690d4af02fc0f8b6a83b8'
serving=R/'runs/known-sortedcontainers-catalog-128-v1/approved-library.json';assert sha(serving)=='738b5337bce44860792bdae22996d225bc22ceb479a5bf1da1da7c0eab4cac9e'
manifest=json.loads((PACK/'manifest.json').read_text());assert sha(PACK/'qualify.py')=='d90952fec65c0c00ec999708d909cf29e8f887c9bc18eefc89f15379c37d8cd2'
for p,h in manifest['inputs_sha256'].items():assert sha(p)==h
reviews={r['id']:r for r in json.loads((OUT/'summary.json').read_text())['reviews']};probes=json.loads((OUT/'semantic-probes.json').read_text());controls=json.loads((OUT/'transport-controls.json').read_text());assert controls['all_expected_outcomes']
FIND.mkdir();data=R/'data/derived/bilingual_development_corpus_v4';(data/'javascript').mkdir(parents=True);(data/'python').mkdir()
# Preserve executable review tooling as read-once artifacts alongside its receipts.
files=['b01-normalize.cjs','b02-normalize.cjs','b01-prepare-style.py','b02-prepare-style.py','b01-b02-check-style.py','b01-b02-contracts.py','b01-b02-domains.py','b01-b02-controls.py','b01-b02-review.py','b01-b02-probes.py','b01-b02-transport-controls.py','publish_b01_b02_catalog_v4.py']
for name in files:shutil.copyfile(T/name,FIND/name)
shutil.copytree(PACK,OUT/'frozen-package')
rows=copy.deepcopy(old['rows']);added=[];batchreports=[]
for batch in ['W001-B01','W001-B02']:
 b=R/'runs/js-corpus-wave-001'/batch;style=json.loads((b/'style-verification.json').read_text());assert len(style['rows'])==20
 batchreport=dict(batch=batch,owner_original_seal=rel(b/'original-source-seal.json'),owner_original_seal_sha256=sha(b/'original-source-seal.json'),style_verification=rel(b/'style-verification.json'),style_verification_sha256=sha(b/'style-verification.json'),qualified_original=style['qualified'],public_mutation_alias_calls=style['differential_calls'],rows=[])
 for assignment in json.loads((PACK/batch/'assignment.json').read_text())['rows']:
  n=assignment['id'];receipt=b/f'{n:04d}/attempt-002/receipt.json';r=json.loads(receipt.read_text());original=b/f'{n:04d}/attempt-001/receipt.json';source=b/f'{n:04d}-role-style.js';packet=json.loads(Path(assignment['problem_packet']).read_text());successor=n in [9,23,30]
  if successor:
   r=reviews[n];assert r['qualified'];source=Path(r['source']);receipt=OUT/f'{n:04d}/review.json';qualified=True
  else:qualified=r['qualified']
  total=assignment['independent_test_count'];provenance=[]
  for ref in assignment['local_sources']:
   assert sha(ref['path'])==ref['sha256'];provenance.append(ref)
  report=dict(id=n,key=assignment['key'],qualified=qualified,independent_total=total,original_receipt=rel(original),original_receipt_sha256=sha(original),selected_receipt=rel(receipt),selected_receipt_sha256=sha(receipt),source=rel(source),source_sha256=sha(source),local_reference_inventory=provenance,reference_review='Compared pinned JS when present, otherwise pinned TypeScript, against owner algorithm and Python behavior. Reference algorithm and side effects need not be identical; owner-source provenance remains separate.',original_qualified=json.loads(original.read_text())['qualified'],successor=successor)
  batchreport['rows'].append(report)
  if not qualified:continue
  assert all(v['python']['passed'] and v['javascript']['passed'] for v in r['results'])
  assert sum(v['python']['tests_total'] for v in r['results'] if v['group'].startswith('independent'))==total
  assert sum(v['javascript']['tests_total'] for v in r['results'] if v['group'].startswith('independent'))==total
  implementations=[]
  for language,src,ext in [('javascript',source,'js'),('python',Path(assignment['python_source']),'py')]:
   dest=data/language/f'{n:04d}.{ext}';dest.write_bytes(src.read_bytes())
   impl=dict(language=language,source=rel(dest),source_input=str(src),source_sha256=sha(src),qualified=True,independent_cases=total,qualification='all public and full frozen assigned independent tests passed under the declared evaluation contract; finite development evidence',qualification_receipt=rel(receipt),qualification_receipt_sha256=sha(receipt),source_provenance=dict(kind='owner-supplied agent candidate; separately authored arithmetic successor' if n==9 and language=='javascript' else 'owner-supplied agent candidate with normalization' if language=='javascript' else 'frozen approved Python reference',owner_source_seal=rel(b/'original-source-seal.json'),owner_source_seal_sha256=sha(b/'original-source-seal.json'),assignment_manifest_sha256=sha(PACK/'manifest.json'),packet_sha256=assignment['problem_packet_sha256'],reference_attribution=packet['attribution'],reference_license=packet['license'],attribution_note='Pinned reference attribution is not a claim that the owner candidate was copied from it.'),semantic_scope=['Existing consumed development cases; not a fresh holdout, formal proof, maximum-bound performance or autonomous solve.','For23 the assigned independent set has only three empty-list cases; three public examples and eight separately derived nonempty control cases are reported separately.'] if n==23 else ['Existing consumed development cases; not a fresh holdout, formal proof, maximum-bound performance or autonomous solve.'])
   if successor:
    impl['evaluation_contract']=dict(path=rel(OUT/'contract.json'),sha256=sha(OUT/'contract.json'),adapter_path=rel(FIND/'b01-b02-contracts.py'),adapter_sha256=sha(FIND/'b01-b02-contracts.py'),change={9:'Native BigInt half-reversal; exact-integer input/output transport; broad integer extension beyond published signed32 range',23:'Decode declared List[Optional[ListNode]] array representations as linked lists; values, node order and expected values unchanged',30:'Outer index order only ignored by multiset comparison; types and multiplicity preserved; expected values unchanged'}[n],chunk_cases=1)
   else:impl['evaluation_contract']=dict(shared_helper_sha256=sha(PACK/'qualify.py'),comparison='unchanged',chunk_cases=16)
   if language=='javascript':
    for field,filename in [('semantics',f'{n:04d}-role-style-semantics.json'),('normalization_receipt',f'{n:04d}-normalization.json'),('style_differential_receipt',f'{n:04d}-style-differential.json')]:impl[field]=rel(b/filename);impl[field+'_sha256']=sha(b/filename)
    impl['style_differential_applies_to_selected']=n!=9
    if n==9:
     semantics=OUT/'0009-successor-semantics.json'
     write(semantics,dict(source_sha256=sha(src),numeric='Native BigInt half-digit reversal, guarded Number input conversion; only boolean output. Never round unsafe input. Exact tagged transport required beyond safe Number.',signature='isPalindrome(x) unchanged',mutation='Local scalar only; no input object mutation or return aliases.',qualification='61 existing independent and3 public cases plus13 independent digit-reversal controls.',owner_original_preserved=True))
     impl['semantics']=rel(semantics);impl['semantics_sha256']=sha(semantics)
   implementations.append(impl)
  new=dict(id=n,key=assignment['key'],independent_cases=total,implementations=implementations);rows.append(new);added.append(n)
 batchreports.append(batchreport)
rows.sort(key=lambda r:r['id']);assert len(rows)==len({r['id'] for r in rows})==len({r['key'] for r in rows})==94
assert len(added)==34 and all(next(r for r in rows if r['id']==p['id'])==p for p in old['rows'])
cases=sum(r['independent_cases'] for r in rows);excluded=sorted(old['excluded_from_catalog_ids']+[1,17,33,39,45,50]);domain=[]
for n in [1,17,33,39,45,50]:
 r=reviews[n];assert not r['qualified'] and r['valid_domain_passed'] and r['all_failures_outside_domain'];q=OUT/f'{n:04d}/quarantine.json';qs=json.loads(q.read_text());domain.append(dict(id=n,full_set_qualified=False,valid_existing_independent=r['valid_independent'],quarantined_independent=r['quarantined_independent'],both_languages_pass_valid_existing=True,all_observed_failures_outside_domain=True,quarantine=rel(q),quarantine_sha256=sha(q),reason_counts=dict(collections.Counter(reason for case in qs for reason in case['reasons'])),review=rel(OUT/f'{n:04d}/review.json'),review_sha256=sha(OUT/f'{n:04d}/review.json'),catalog_admitted=False))
catalog=dict(schema='algsolve.bilingual-development-corpus.v4',scope=old['scope'],predecessor=dict(path=rel(prior),sha256=sha(prior),unique_problems=60,rows_preserved_exactly=True),unique_problems=94,implementations=188,language_implementations={'javascript':94,'python':94},independent_cases_per_language=cases,paired_independent_execution_count=cases*2,added_unique=34,added_ids=sorted(added),excluded_from_catalog_ids=excluded,domain_scoped_results_included_in_catalog_count=False,duplicate_ids=0,duplicate_keys=0,autonomous_new_solves=0,source_policy=old['source_policy'],rows=rows)
write(FIND/'catalog.json',catalog);write(R/'data/derived/bilingual_development_catalog_v4.json',catalog);write(R/'data/derived/javascript_development_catalog_v4.json',dict(schema='algsolve.javascript-development-corpus.v4',unique_problems=94,independent_cases=cases,rows=[dict(id=r['id'],key=r['key'],**next(i for i in r['implementations'] if i['language']=='javascript')) for r in rows]))
write(FIND/'batch-review.json',dict(batches=batchreports,domain_review=domain,scope='Primary128 source review; no claim of independent second-agent or human review.',no_external_zip_received=True,local_owner_test_claims_not_evidence=True))
integration=dict(base_commit='2558e83f80c16da33b4dc848af965f04d3b03ce5',prior_catalog_sha256=sha(prior),prior_rows_unchanged=True,catalog_sha256=sha(FIND/'catalog.json'),unique_before=60,added=34,unique_after=94,implementations=188,independent_cases_per_language=cases,added_independent_cases_per_language=cases-5289,original_qualified=31,separate_successors=[9,23,30],new_full_set_exclusions=[1,17,33,39,45,50],valid_existing_domain_cases=sum(r['valid_existing_independent'] for r in domain),quarantined_independent_cases=sum(r['quarantined_independent'] for r in domain),normalization_public_runtime_calls=107,additional_semantic_runtime_calls=probes['original_normalized_runtime_calls'],software_control_groups=9,exact_integer_controls=13,float_controls=6,collection_mutant_rejections=6,nested_node_control_cases=8,index_comparator_adversarial_cases=6,transport_control_language_executions=28,production_catalog_sha256=sha(serving),production_catalog_unchanged=True,protected_opened=False,public_push=False,public_deployment=False)
write(FIND/'integration.json',integration)
for row in rows:
 for impl in row['implementations']:
  assert sha(R/impl['source'])==impl['source_sha256'];assert subprocess.run(['git','check-ignore',str(R/impl['source'])],cwd=REPO,stdout=subprocess.DEVNULL).returncode==0
assert sha(serving)=='738b5337bce44860792bdae22996d225bc22ceb479a5bf1da1da7c0eab4cac9e'
print(json.dumps(integration,indent=2))
