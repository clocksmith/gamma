from pathlib import Path
import collections,copy,hashlib,json,subprocess
REPO=Path('/home/x/deco/gamma');ROOT=REPO/'projects/algorithm_solver';FIND=ROOT/'findings/js-corpus-subset-domain-128-v1';OUT=ROOT/'runs/js-corpus-subset-domain-128-v1';PACK=Path('/home/x/Documents/Codex/2026-10-19/task/js-corpus-wave-001')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rel=lambda p:str(Path(p).relative_to(ROOT))
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()=='bb491e95a38c12ae42f9273adcaa526a63153dca'
previous=ROOT/'findings/js-corpus-b03-b04-integration-128-v1/catalog.json';previous_hash=sha(previous);old=json.loads(previous.read_text());assert old['unique_problems']==58 and old['independent_cases_per_language']==5095
summary=json.loads((OUT/'summary.json').read_text());byid={r['id']:r for r in summary['rows']};controls=json.loads((OUT/'comparator-adversarial-controls.json').read_text());assert controls['all_expected_outcomes'] and controls['fixtures']==12 and controls['language_executions']==24
assert summary['old58_catalog_unchanged'] and summary['raw_oracles_unchanged']
oracle=json.loads((OUT/'independent-oracle-summary.json').read_text());oracle_byid={r['id']:r for r in oracle['rows']};rows=copy.deepcopy(old['rows'])
data=ROOT/'data/derived/bilingual_development_corpus_v3';(data/'javascript').mkdir(parents=True);(data/'python').mkdir()
assignments=json.loads((PACK/'W001-B04/assignment.json').read_text())['rows'];newrows=[]
for n in [78,90]:
 r=byid[n];assert r['qualified'] and r['catalog_admission_authorized'] and r['quarantined_independent']==0
 assert r['evaluated_independent']==r['original_independent_total']==r['python_independent_passed']==r['javascript_independent_passed']
 assert r['public_total']==r['public_evaluated']==r['public_passed']==2
 assignment=next(a for a in assignments if a['id']==n);batch=ROOT/'runs/js-corpus-wave-001/W001-B04';packet=json.loads(Path(assignment['problem_packet']).read_text());receipt=OUT/f'{n:04d}/summary.json';implementations=[]
 for language,source,key in [('javascript',Path(r['source']),'source_sha256'),('python',Path(r['python_source']),'python_source_sha256')]:
  assert sha(source)==r[key];dest=data/language/f"{n:04d}.{'js' if language=='javascript' else 'py'}";dest.write_bytes(source.read_bytes())
  impl=dict(language=language,source=rel(dest),source_input=str(source),source_sha256=sha(dest),qualified=True,independent_cases=r['evaluated_independent'],qualification='public-and-full-existing-independent-tests-passed under separately versioned outer-orderv2; development only',qualification_receipt=rel(receipt),qualification_receipt_sha256=sha(receipt),evaluation_contract=dict(path=rel(OUT/'contract.json'),sha256=sha(OUT/'contract.json'),comparison='return:unordered_outer',comparator_path='findings/js-corpus-b03-b04-integration-128-v1/subset_order_v2.py',comparator_sha256=sha(ROOT/'findings/js-corpus-b03-b04-integration-128-v1/subset_order_v2.py'),chunk_cases=1,preserve='inner order, exact types and multiplicity; expected values unchanged'),source_provenance=dict(kind='owner-supplied agent candidate with role-style normalization' if language=='javascript' else 'frozen approved Python reference',packet_sha256=assignment['problem_packet_sha256'],attribution=packet['attribution'],license=packet['license']),semantic_scope='Finite existing development tests; no new source generation, generalization, performance-bound or autonomous-solving claim.')
  if language=='javascript':
   for field,filename in [('normalization_receipt',f'{n:04d}-normalization.json'),('style_differential_receipt',f'{n:04d}-style-differential.json'),('semantics',f'{n:04d}-role-style-semantics.json')]:impl[field]=rel(batch/filename);impl[field+'_sha256']=sha(batch/filename)
   impl['historical_failed_receipt']=rel(batch/f'{n:04d}/attempt-002/receipt.json');impl['historical_failed_receipt_sha256']=sha(batch/f'{n:04d}/attempt-002/receipt.json')
  implementations.append(impl)
 newrows.append(dict(id=n,key=r['key'],independent_cases=r['evaluated_independent'],implementations=implementations))
rows=sorted(rows+newrows,key=lambda r:r['id']);assert len(rows)==len({r['id'] for r in rows})==len({r['key'] for r in rows})==60
assert sum(r['independent_cases'] for r in rows)==5289
assert all(next(r for r in rows if r['id']==before['id'])==before for before in old['rows'])
catalog=dict(schema='algsolve.bilingual-development-corpus.v3',scope=old['scope'],predecessor=dict(path=rel(previous),sha256=previous_hash,unique_problems=58,rows_preserved_exactly=True),unique_problems=60,implementations=120,language_implementations={'javascript':60,'python':60},independent_cases_per_language=5289,paired_independent_execution_count=10578,added_unique=2,added_ids=[78,90],excluded_from_catalog_ids=[60,65,74,81,87],separately_domain_scoped_qualified_ids=[60,65,74,81,87],domain_scoped_results_included_in_catalog_count=False,duplicate_ids=0,duplicate_keys=0,autonomous_new_solves=0,source_policy=old['source_policy'],rows=rows)
write(FIND/'catalog.json',catalog);write(ROOT/'data/derived/bilingual_development_catalog_v3.json',catalog)
write(ROOT/'data/derived/javascript_development_catalog_v3.json',dict(schema='algsolve.javascript-development-corpus.v3',unique_problems=60,implementations=60,independent_cases=5289,rows=[dict(id=r['id'],key=r['key'],**next(i for i in r['implementations'] if i['language']=='javascript')) for r in rows]))
domain=[]
for n in [60,65,74,81,87]:
 r=byid[n];verification=oracle_byid[n];quarantine=json.loads((OUT/f'{n:04d}-quarantine.json').read_text());assert r['qualified'] and verification['all_expected_verified']
 assert verification['independent_checked']==r['evaluated_independent'] and verification['public_checked']==r['public_evaluated']==r['public_total']
 domain.append(dict(id=n,original_independent=r['original_independent_total'],valid_existing_independent=r['evaluated_independent'],quarantined_independent=r['quarantined_independent'],public_passed=r['public_passed'],both_languages_passed=True,independent_expectations_verified=True,quarantine_reason_counts=dict(collections.Counter(reason for q in quarantine for reason in q['reasons'])),selection_seal=rel(OUT/f'{n:04d}-selection-seal.json'),selection_seal_sha256=sha(OUT/f'{n:04d}-selection-seal.json'),quarantine=rel(OUT/f'{n:04d}-quarantine.json'),quarantine_sha256=sha(OUT/f'{n:04d}-quarantine.json'),qualification_receipt=rel(OUT/f'{n:04d}/summary.json'),qualification_receipt_sha256=sha(OUT/f'{n:04d}/summary.json'),oracle_verification=rel(OUT/f'{n:04d}-independent-oracle-verification.json'),oracle_verification_sha256=sha(OUT/f'{n:04d}-independent-oracle-verification.json'),assessment='Existing cases suffice for explicitly scoped, finite valid-published-domain regression qualification: nonempty independently checked expectations, all public cases, both languages passing. They do not satisfy the unchanged historical full-set gate; do not imply fresh holdout success, full-domain proof or performance coverage.',catalog_admitted=False))
assert sum(d['valid_existing_independent'] for d in domain)==597 and sum(d['quarantined_independent'] for d in domain)==96
write(FIND/'domain-review.json',dict(rows=domain,valid_independent=597,quarantined_independent=96,total_original_independent=693,public_cases=13,selection_outcome_blind=True,expected_values_rewritten=False,quarantined_cases_deleted=False,scope='These597 cases are existing consumed development cases, not new coverage. Domain filters cover all pinned structural/type/size/range constraints and were tested before selection.'))
integration=dict(base_commit='bb491e95a38c12ae42f9273adcaa526a63153dca',previous_catalog_sha256=previous_hash,previous58_rows_unchanged=True,successor_catalog_sha256=sha(FIND/'catalog.json'),unique_before=58,added_unique=2,unique_after=60,implementations=120,independent_cases_per_language=5289,new_subset_independent_cases=194,new_subset_public_cases=4,comparator_adversarial_fixtures=12,comparator_adversarial_language_executions=24,domain_software_control_groups=7,independent_oracle_control_groups=5,domain_valid_existing_cases=597,domain_quarantine_cases=96,domain_scoped_cases_added_to_catalog=False,raw_oracles_unchanged=True,shared_wave_helper_unchanged=True,protected_opened=False,other_owner_batches_touched=False,public_push=False,public_deployment=False)
assert sha(previous)==previous_hash
write(FIND/'integration.json',integration)
table='\n'.join(f"| {d['id']} | {d['valid_existing_independent']}/{d['original_independent']} | {d['quarantined_independent']} | {d['public_passed']} |" for d in domain)
readme='''# Subset admission and explicit domain quarantine

The successor [catalog](catalog.json) admits78/90 only under the existing isolated
outer-orderv2 comparator. It contains **60 unique problems**,60 JavaScript and60
Python implementations, with **5,289 matched independent cases per language**.
The predecessor58 catalog hash and all58 rows remain unchanged. Raw code remains
private; new bodies are under `data/derived/bilingual_development_corpus_v3/` and
the successor index is `data/derived/bilingual_development_catalog_v3.json`.

Fresh unchanged-source reruns pass91/91 and103/103 independent cases in both
languages, plus four public cases. Twelve adversarial fixtures run through both
language transports verify accepted reorderings and rejected missing,extra,
duplicated,replaced,wrong-shaped,wrong-typed and multiplicity-losing outputs.
The comparator uses a multiset, not deduplicating sets; inner order,types and
multiplicity remain strict. Historical failed attempts and expected values remain
intact. One case per invocation retains the64KiB per-invocation output cap.

## Five remaining domains

[Domain evidence](domain-review.json) records an outcome-blind selection sealed
before evaluation. The pinned HTML statements corroborate exponent bounds lost
in plain-text imports. Seven classifier-control groups include exhaustive rotation
checks for363 small arrays. Every excluded case remains in a hash-bound quarantine
with its original input,expected value,index and reasons; no case was deleted.

| ID | Valid existing independent cases | Quarantined | Public cases passed |
|---|---:|---:|---:|
'''+table+'''

All597 retained independent cases and13 public cases pass both languages.
Independent formulations verify every retained expectation: direct permutation
enumeration, a numeric grammar state machine, linear membership and bottom-up
scramble DP. Five software-control groups passed before those oracle checks.
These are **existing consumed development cases**, not newly acquired coverage.

They suffice for a named **finite valid-published-domain regression qualification**,
with the exact denominators above. They do not pass the unchanged historical
full-set gate, prove full-domain correctness, establish maximum-bound performance,
or provide fresh holdout evidence. The five remain outside this60-entry catalog;
their scoped results are reported separately rather than silently narrowing claims.

No new broad batch, protected evaluation, predictor campaign, production loader
change, public push or deployment. B01/B02 owner work remains untouched.
'''
(FIND/'README.md').write_text(readme)
status=ROOT/'STATUS.md';text=status.read_text();marker='## Integrated bilingual development corpus:58 unique problems\n';assert marker in text
addition='''## Successor bilingual development corpus:60 unique problems

The [v3 catalog](findings/js-corpus-subset-domain-128-v1/catalog.json) preserves all58
predecessor rows and adds78/90 after fresh both-language runs under the separately
versioned outer-order comparator:60 problems,120 implementations,5,289 matched
independent cases per language. Twelve adversarial comparator fixtures passed in
both runtimes; missing or duplicate subsets remain rejected.

The [domain review](findings/js-corpus-subset-domain-128-v1/README.md) retains96
invalid-domain cases across60/65/74/81/87 in explicit quarantine. Both languages
pass597 remaining existing cases and13 public examples, with independently
verified expectations. That is explicitly scoped domain-regression evidence;
these five remain excluded from the60-entry catalog. No historical artifact,
production serving path, other owner batch or protected test was changed.

'''
status.write_text(text.replace(marker,addition+marker));print(json.dumps(integration,indent=2))
