from pathlib import Path
import hashlib,json,sys
ROOT=Path('/home/x/deco/gamma/projects/algorithm_solver');FIND=ROOT/'findings/js-corpus-b03-b04-integration-128-v1';RUN=ROOT/'runs/js-corpus-contract-review-128-v1';PACK=Path('/home/x/Documents/Codex/2026-10-19/task/js-corpus-wave-001')
sys.path[:0]=[str(ROOT),str(ROOT/'findings/js-exact-integer-transport-128-v1')]
from algsolve import validate
from algsolve.records import Problem,load_hidden_tests
from algsolve.judge import judge,sandbox
import exact_integer
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
reviews=json.loads((RUN/'review-summary.json').read_text());metadata=[];lines=['# B03/B04 exact contract review','', 'Pinned statements and approved Python sources are the authority for input domains. Raw expected values, original candidates, historical modes and receipts remain unchanged. The full ordered-disagreements files contain every mismatching single-case re-score for78/90, with exact inputs, expected values and both actual results. Historical aggregate output-limit failures remain separate from these re-scores.','']
rules={60:'1 <= n <= 9;1 <= k <= n!. Python subtracts factorial blocks and eventually returns a shorter string for an impossible rank. JavaScript splices an absent digit and concatenates undefined. Neither behavior is a specified answer outside the domain.',65:'s must be a string of English letters,digits,+,-,dot. Python happens to inspect the one-element list and return false; JavaScript raises TypeError at trim. No in-domain candidate failure was established by this case. trim also accepts surrounding whitespace, but whitespace is outside this pinned domain.',74:'Rows must be nondecreasing and each row first value strictly greater than the previous row last. Both matrices violate these preconditions. Python lower-bound search misses an existing target; JavaScript early-hit search happens to find it. A linear membership oracle would return true, but silently extending the domain is not authorized.',81:'nums must be a rotation of a nondecreasing sequence. The descending ten-element input cannot satisfy that property. Python happens to find the final element; JavaScript does not. Neither binary-search implementation promises general unsorted membership.',87:'The two lowercase strings must have equal length. Both failing pairs have lengths10 and12. Python recurses over only len(s1), ignoring extra suffix positions; JavaScript rejects the length mismatch. The true expectations do not describe valid scrambling of unequal-length strings.',78:'The solution can be returned in any order. Identical [1,2,3] input has conflicting exact outer orders across public and independent tests. Python and JavaScript produce the same subset collection. The shared wave comparison declaration is defective; the base comparator correctly follows its ordered declaration.',90:'The solution can be returned in any order. Identical [1,2,2] and[0] inputs have conflicting exact outer orders. Both languages produce the same duplicate-free subset collection. The shared wave comparison declaration is defective; the base comparator correctly follows its ordered declaration.'}
for r in reviews['reviews']:
 n=r['id'];lines += [f'## {n}',rules[n],'',f"Classification: {r['classification']}",'',f"Statement: {r['statement_packet']} (SHA256 {r['statement_packet_sha256']}).",f"Python: {r['python_source']} (SHA256 {r['python_source_sha256']}).",f"JavaScript: {r['javascript_source']} (SHA256 {r['javascript_source_sha256']}).",'']
 meta={k:r[k] for k in ['id','key','classification','statement_packet','statement_packet_sha256','attribution','python_source','python_source_sha256','javascript_source','javascript_source_sha256']};meta['assessment']=rules[n];meta['raw_review']=str((RUN/f'{n:04d}/review.json').relative_to(ROOT));meta['raw_review_sha256']=sha(RUN/f'{n:04d}/review.json')
 if 'failing_cases' in r:
  for c in r['failing_cases']:
   exact={k:c[k] for k in ['index','input','expected','python_actual','javascript_actual','domain_conflict']}
   lines += ['```json',json.dumps(exact,indent=2),'```','']
  meta['failing_case_count']=len(r['failing_cases']);meta['expected_values_changed']=False;meta['integration']='excluded'
 else:
  rawproblem=next(json.loads(l) for l in (ROOT/'data/derived/problems.jsonl').read_text().splitlines() if json.loads(l)['uid']==f'lcd:{n}');p=Problem.from_dict(rawproblem);tests=load_hidden_tests(p)
  row=next(x for x in json.loads((PACK/'W001-B04/assignment.json').read_text())['rows'] if x['id']==n);packet=json.loads(Path(row['problem_packet']).read_text());failures=[]
  for group,rawtests in [('public',packet['public_tests']),('independent',tests)]:
   for i,test in enumerate(rawtests):
    pybytes=(RUN/f'{n:04d}/{group}-{i:03d}-python.jsonl').read_bytes();jsbytes=(RUN/f'{n:04d}/{group}-{i:03d}-javascript.jsonl').read_bytes();ts=validate.functional_tests([test])
    py=judge._score_functional(sandbox.SandboxResult(0,None,pybytes,b'',0),ts);js=exact_integer.score_result(sandbox.SandboxResult(0,None,jsbytes,b'',0),ts)
    if not py.passed or not js.passed:
     failures.append(dict(group=group,index=i,input=test['args'],expected=test['expected'],python_actual=json.loads(pybytes.splitlines()[0]),javascript_actual=json.loads(jsbytes.splitlines()[0]),python_ordered_passed=py.passed,javascript_ordered_passed=js.passed,comparison='historical return mode; re-score of the same source under single-case transport'))
  target=RUN/f'{n:04d}/ordered-disagreements.json';write(target,failures)
  lines += [f"Corrected outer-order contract: Python and JavaScript both pass all {r['public_total']} public and {r['independent_total']} independent cases. Source and expected values are unchanged. Eight independent comparison-control groups passed. Inner order,types,multiplicity and protocol failure behavior remain strict.",'',f"Complete exact ordered disagreements: {target}",'']
  for c in r['comparison_conflicts']:
   lines+=['```json',json.dumps({k:c[k] for k in ['group','index','input','expected','python_actual','javascript_actual']},indent=2),'```','']
  meta.update(corrected_qualified=r['qualified_under_v2'],public_total=r['public_total'],independent_total=r['independent_total'],python_independent_passed=r['python_independent_passed'],javascript_independent_passed=r['javascript_independent_passed'],complete_ordered_disagreements=str(target.relative_to(ROOT)),complete_ordered_disagreements_sha256=sha(target),integration='separately qualified; not included in specifically requested33+115 integration')
 metadata.append(meta)
(RUN/'EXACT_REVIEW.md').write_text('\n'.join(lines)+'\n');write(FIND/'conflict-review.json',dict(rows=metadata,exact_report=str((RUN/'EXACT_REVIEW.md').relative_to(ROOT)),exact_report_sha256=sha(RUN/'EXACT_REVIEW.md'),scope='No domain filtering, oracle rewrites, candidate hacks or historical result replacements.'))
write(FIND/'115-review.json',reviews['review115'])
readme='''# B03/B04 bilingual corpus integration

The versioned [catalog](catalog.json) contains **58 unique problems** with58 JavaScript
and58 Python implementations. It preserves the24-problem predecessor and adds the
requested33 B03/B04 candidates plus115 after its exact-integer contract review.
There are5,095 matched independent cases per language; this is10,190 language
executions, not10,190 unique test cases. IDs and language-agnostic keys are deduplicated.

[Integration evidence](integration.json) binds sources, provenance, normalization,
test and receipt hashes. The private bodies are in
`data/derived/bilingual_development_corpus_v2/{javascript,python}/`; the index is
`data/derived/bilingual_development_catalog_v2.json`. A JS-onlyv2 index is also
available. No production loader or Python recognition catalog changes.

## Seven conflicts reviewed

[Per-ID conclusions and source evidence](conflict-review.json) link the
[exact private report](../../runs/js-corpus-contract-review-128-v1/EXACT_REVIEW.md),
which includes failing inputs, expected values and both actual results.60,65,74,81
and87 have nine failing test rows outside their pinned input domains. Python's
incidental match on those cases does not establish an in-domain candidate bug or
a legitimate generalized oracle. All five remain excluded; no expected value was
rewritten and no failing case was silently removed.

78 and90 have a genuine shared-wave contract defect: exact outer-array ordering
contradicts the statements and even gives conflicting expectations for identical
inputs. The isolated [v2 correction](subset_order_v2.py) changes only the comparison
declaration for the exact uid/slug/method identities. It reuses the tested
multiset comparator, retaining inner order,types and multiplicity. One case per
sandbox invocation avoids aggregate output truncation without raising the64KiB
cap. [Eight independent control groups](test_subset_order_v2.py) pass. Unchanged
original algorithms in both languages pass91/91 and103/103 independent cases and
all four public cases. These two corrected results remain separate from the
explicitly requested33+115 integration; the integrated count is58, not60.

## Exact-integer115 review

[115 review](115-review.json) verifies all existing transport/runner hashes, the
101/101 independent results in both languages, two public cases and four input
preservation probes. Five additional combinatorial checks use independently
derived binomial coefficients, including60-choose30 and100-choose50. Native
BigInt results remain exact; unsafe Number output is rejected. This qualifies
the explicit BigInt-capable development implementation, not arbitrary runtimes.

The33 B03/B04 additions have2,777 independent cases. Their style-only ancestors
preserve all40 original qualification outcomes and95 public result/mutation/
reference-alias observations;62/69 are explicitly separate numeric successors.
The prior B04 console count1849 was a label typo: the actual frozen assignment
and receipts contain1749 cases. No test selection changed.

The next lane is broader paired-corpus coverage and semantic macro discovery.
Histogram stack84/85 and inorder94/98 are candidate shared patterns, not newly
qualified macros. There is no new predictor campaign, training, protected scoring,
public push, deployment, autonomous solve or language-codebook promotion here.
'''
(FIND/'README.md').write_text(readme)
status=ROOT/'STATUS.md';s=status.read_text();marker='## Integrated JavaScript corpus: B05 only\n';assert marker in s
addition='''## Integrated bilingual development corpus:58 unique problems

The [v2 catalog](findings/js-corpus-b03-b04-integration-128-v1/catalog.json)
preserves the24-entry predecessor and adds33 reviewed B03/B04 candidates plus115
after exact-integer review:58 JavaScript and58 Python implementations, with5,095
matched independent cases per language. Raw sources remain private. This changes
the corpus for semantic macro discovery, not production recognition or the app.

[Seven-conflict review](findings/js-corpus-b03-b04-integration-128-v1/README.md)
retains five invalid-domain failures. The isolated outer-order correction for78/90
passes91/91 and103/103 in both languages without source or expected-value edits;
those two remain separate review results, outside the requested33+115 integration.
Historical catalogs, failures, other owners' batches and protected tests remain intact.

'''
status.write_text(s.replace(marker,addition+marker))
print('Exact private seven-ID review, tracked source-evidence summary,115 review and status written.')
