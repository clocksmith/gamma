"""Link an audited accepted vocabulary prefix to a qualified source/primitive union."""
import argparse,json
from pathlib import Path
from search import joint
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--prior-freeze',type=Path,required=True);p.add_argument('--prior-run',type=Path,required=True);p.add_argument('--review',type=Path,required=True);p.add_argument('--supply',type=Path,required=True);p.add_argument('--helpers',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
old=(a.prior_freeze/'contract.json').read_bytes();c=json.loads(old);review=json.loads(a.review.read_bytes())
if review['status'] not in ('verified','verified_prefix') or review['contract_sha256']!=joint.b.sha(old):raise ValueError('independent accepted-prefix review mismatch')
for name,key in [('ledger.jsonl','ledger_sha256'),('costs.jsonl','costs_sha256')]:
 if joint.b.sha((a.prior_run/name).read_bytes())!=review[key]:raise ValueError('reviewed prefix changed')
events=[json.loads(x) for x in (a.prior_run/'ledger.jsonl').read_text().splitlines()];anchor=events[-1]
if anchor['sha256']!=review['ledger_head']:raise ValueError('accepted head mismatch')
sraw=a.supply.read_bytes();supply=json.loads(sraw);hraw=a.helpers.read_bytes();audit=json.loads(hraw)
if supply['fit_population']!=300 or supply['protected_access'] is not False or supply['validation_source_reads']!=0 or audit['protected_access'] is not False:raise ValueError('supply/audit scope drift')
for key in ['fit_ids','families','references']:
 if supply[key]!=c[key]:raise ValueError('problem/reference/family identity changed')
for key,row in c['source_rows'].items():
 if supply['source_rows'][key]['sha256']!=row['sha256']:raise ValueError('predecessor source removed or changed')
for name,h in supply['code_sha256'].items():
 if joint.b.sha((HERE.parent/name).read_bytes())!=h:raise ValueError('qualified supply code changed')
for row in supply['source_rows'].values():
 if joint.b.sha(Path(row['path']).read_bytes())!=row['sha256']:raise ValueError('qualified source bytes changed')
if len(audit['allowed'])!=8:raise ValueError('expected exact reviewed primitive scope')
pins={n:joint.b.sha((HERE/n).read_bytes()) for n in ['search.py','run.py','prepare.py','accelerator.py','score_kernel.c','FREEZE.md','test_search.py','test_accelerator.py','../incremental-merge-v2/search.py','../incremental-merge-v1/search.py']}
deps=json.loads(Path('/workspace/shared/gamma-dot-diagnostics/incremental-engine-dependency-pins.json').read_text())['code_sha256']
for name,h in {**deps,**supply['code_sha256']}.items():
 if joint.b.sha((HERE.parent/name).read_bytes())!=h:raise ValueError('dependency drift')
 pins['../'+name]=h
kernel=Path('/workspace/shared/gamma-dot-diagnostics/score_trie_kernel.so')
proofs=[]
for name in ['trie-kernel-validation.json','trie-kernel-validation-256.json']:
 path=Path('/workspace/shared/gamma-dot-diagnostics')/name
 evidence=json.loads(path.read_bytes())
 if evidence['exact_rows_equal'] is not True or evidence['full_source_rows_and_cached_remove_rows_equal'] is not True or evidence['source_variants']!=len(supply['source_rows']) or evidence['source_supply_sha256']!=joint.b.sha(sraw) or evidence['candidate_executions']!=0 or evidence['protected_access'] is not False:raise ValueError('invalid scorer equivalence evidence')
 if evidence['kernel_source_sha256']!=joint.b.sha((HERE/'score_kernel.c').read_bytes()) or evidence['kernel_binary_sha256']!=joint.b.sha(kernel.read_bytes()) or evidence['adapter_sha256']!=joint.b.sha((HERE/'accelerator.py').read_bytes()):raise ValueError('scorer equivalence artifact drift')
 proofs.append({'path':str(path),'sha256':joint.b.sha(path.read_bytes())})
c.update({'schema':'gamma.incremental-qualified-primitive-union.v3','code_sha256':pins,'source_rows':supply['source_rows'],'owners':supply['owners'],'initial_learned':anchor['learned_literals'],'initial_frontier':[],'predecessor_frontier':anchor['frontier'],'predecessor_metrics':anchor['metrics'],'predecessor_contract_sha256':joint.b.sha(old),'predecessor_ledger_head':review['ledger_head'],'predecessor_ledger_sha256':review['ledger_sha256'],'predecessor_costs_sha256':review['costs_sha256'],'predecessor_review_sha256':joint.b.sha(a.review.read_bytes()),'predecessor_status':'accepted-prefix; paused, no exhaustion claim','source_supply_sha256':joint.b.sha(sraw),'source_supply_path':str(a.supply),'helper_audit_sha256':joint.b.sha(hraw),'audited_helpers':audit['allowed'],'excluded_helpers':audit['excluded'],'kernel_path':str(kernel),'kernel_source_sha256':joint.b.sha((HERE/'score_kernel.c').read_bytes()),'kernel_binary_sha256':joint.b.sha(kernel.read_bytes()),'kernel_equivalence_proofs':proofs,'engine_successor':'pre-load hash-checked trie exact canonical DP','policy_successor':'same adjacent-parent consolidation plus exact audited primitive union/retirement; qualified source expansion'})
a.output.mkdir(parents=True,exist_ok=False);joint.b.write(a.output/'contract.json',c);print(json.dumps({'status':'frozen','source_variants':len(c['source_rows']),'initial_entries':96+len(c['initial_learned']),'audited_primitives':8}))
