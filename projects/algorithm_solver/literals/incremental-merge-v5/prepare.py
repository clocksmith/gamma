"""Freeze exact pruning acceleration against a reviewed accepted branch prefix."""
import argparse,ast,json,os
from pathlib import Path
from search import joint
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--prior-freeze',type=Path,required=True);p.add_argument('--prior-run',type=Path,required=True);p.add_argument('--review',type=Path,required=True);p.add_argument('--capacity',type=int,choices=[128,256],required=True);p.add_argument('--winner-proof',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
old=(a.prior_freeze/'contract.json').read_bytes();c=json.loads(old);review=json.loads(a.review.read_bytes());proof=json.loads(a.winner_proof.read_bytes())
if review['status'] not in ('verified','verified_prefix') or review['contract_sha256']!=joint.b.sha(old):raise ValueError('accepted-prefix audit mismatch')
for name,key in [('ledger.jsonl','ledger_sha256'),('costs.jsonl','costs_sha256')]:
 if joint.b.sha((a.prior_run/name).read_bytes())!=review[key]:raise ValueError('reviewed prefix changed')
events=[json.loads(x) for x in (a.prior_run/'ledger.jsonl').read_text().splitlines()];anchor=events[-1]
if anchor['sha256']!=review['ledger_head']:raise ValueError('accepted head mismatch')
if proof['status']!='verified' or proof['contract_sha256']!=joint.b.sha(old) or not all(proof[k] is True for k in ['exact_recorded_winner_equal','source_choices_equal','dictionary_equal']) or proof['source_variants']!=len(c['source_rows']) or proof.get('all_source_counts_equal') is not True or proof.get('all_source_count_rows')!=len(c['source_rows']) or proof['candidate_executions']!=0 or proof['protected_access'] is not False:raise ValueError('real exact-winner proof missing')
for name,h in proof['code_sha256'].items():
 if joint.b.sha((HERE/name).read_bytes())!=h:raise ValueError('verified count-only implementation changed')
pins={n:joint.b.sha((HERE/n).read_bytes()) for n in ['search.py','run.py','prepare.py','accelerator.py','score_kernel.c','FREEZE.md','test_counts.py']}
prior_root=HERE.parent/'incremental-merge-v4'
for name,h in c['code_sha256'].items():
 path=(prior_root/name).resolve()
 if joint.b.sha(path.read_bytes())!=h:raise ValueError('predecessor dependency changed')
 pins[os.path.relpath(path,HERE)]=h
c.update({'schema':'gamma.incremental-deferred-trace.v5','code_sha256':pins,'branch_capacity':a.capacity,'initial_learned':anchor['learned_literals'],'initial_frontier':anchor['frontier'],'predecessor_contract_sha256':joint.b.sha(old),'predecessor_ledger_head':review['ledger_head'],'predecessor_ledger_sha256':review['ledger_sha256'],'predecessor_costs_sha256':review['costs_sha256'],'predecessor_review_sha256':joint.b.sha(a.review.read_bytes()),'predecessor_metrics':anchor['metrics'],'predecessor_status':'accepted prefix, paused not exhausted','exact_winner_proof_sha256':joint.b.sha(a.winner_proof.read_bytes()),'exact_winner_proof_path':str(a.winner_proof),'policy_successor':'no search-policy change; deferred trace reconstruction with exact counts and full accepted-state worklists'})
a.output.mkdir(parents=True,exist_ok=False);joint.b.write(a.output/'contract.json',c);print(json.dumps({'status':'frozen','capacity':a.capacity,'initial_entries':96+len(c['initial_learned']),'source_variants':len(c['source_rows'])}))
