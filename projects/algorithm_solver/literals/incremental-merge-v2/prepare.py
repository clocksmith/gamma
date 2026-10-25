"""Freeze a consolidation successor of an independently reviewed vocabulary."""
import argparse,json
from pathlib import Path
from search import joint
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--prior-freeze',type=Path,required=True);p.add_argument('--prior-run',type=Path,required=True);p.add_argument('--review',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
old=(a.prior_freeze/'contract.json').read_bytes();c=json.loads(old);review=json.loads(a.review.read_bytes())
if review['status']!='verified' or review['contract_sha256']!=joint.b.sha(old):raise ValueError('independent predecessor review mismatch')
for name,key in [('ledger.jsonl','ledger_sha256'),('costs.jsonl','costs_sha256')]:
 if joint.b.sha((a.prior_run/name).read_bytes())!=review[key]:raise ValueError('reviewed ledger changed')
result=json.loads((a.prior_run/'results.json').read_text());state=json.loads((a.prior_run/'final-state.json').read_text());events=[json.loads(x) for x in (a.prior_run/'ledger.jsonl').read_text().splitlines()]
if result['status']!='completed' or result['ledger_head']!=review['ledger_head'] or events[-1]['sha256']!=review['ledger_head']:raise ValueError('predecessor not completed/reviewed')
if state['learned_literals']!=events[-1]['learned_literals'] or state['choices']!=events[-1]['source_choices']:raise ValueError('initial vocabulary identity drift')
deps=json.loads(Path('/workspace/shared/gamma-dot-diagnostics/incremental-engine-dependency-pins.json').read_text())['code_sha256']
pins={n:joint.b.sha((HERE/n).read_bytes()) for n in ['search.py','run.py','prepare.py','accelerator.py','score_kernel.c','FREEZE.md','test_search.py','test_accelerator.py','../incremental-merge-v1/search.py']}
for name,h in deps.items():
 path=HERE.parent/name
 if joint.b.sha(path.read_bytes())!=h:raise ValueError('upstream dependency changed')
 pins['../'+name]=h
c.update({'schema':'gamma.incremental-composition-retirement.v2','code_sha256':pins,'initial_learned':state['learned_literals'],'initial_frontier':events[-1]['frontier'],'predecessor_contract_sha256':joint.b.sha(old),'predecessor_ledger_head':review['ledger_head'],'predecessor_ledger_sha256':review['ledger_sha256'],'predecessor_costs_sha256':review['costs_sha256'],'predecessor_review_sha256':joint.b.sha(a.review.read_bytes()),'predecessor_results_sha256':joint.b.sha((a.prior_run/'results.json').read_bytes()),'kernel_path':'/workspace/shared/gamma-dot-diagnostics/score_kernel.so','kernel_source_sha256':joint.b.sha((HERE/'score_kernel.c').read_bytes()),'kernel_binary_sha256':joint.b.sha(Path('/workspace/shared/gamma-dot-diagnostics/score_kernel.so').read_bytes()),'engine_successor':'pre-load hash-checked exact canonical C DP','policy_successor':'adjacent composition plus optional learned-parent retirement; same source choice and gate ordering'})
a.output.mkdir(parents=True,exist_ok=False);joint.b.write(a.output/'contract.json',c);print(json.dumps({'status':'frozen','source_variants':len(c['source_rows']),'initial_entries':96+len(c['initial_learned'])}))
