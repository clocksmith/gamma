"""Qualified compact alternatives, same exact optimizer and accepted dictionary."""
import argparse,importlib.util,json,os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;LIT=HERE.parent;CORE=LIT/'incremental-merge-v5'
sys.path.insert(0,str(CORE));import search,accelerator
spec=importlib.util.spec_from_file_location('compact_source_verifier',LIT/'compact-variants-v1/verify.py');verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)
b=search.joint.b
p=argparse.ArgumentParser();p.add_argument('--prior-freeze',type=Path,required=True);p.add_argument('--prior-run',type=Path,required=True);p.add_argument('--review',type=Path,required=True);p.add_argument('--inputs',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--node',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
raw=(a.prior_freeze/'contract.json').read_bytes();c=json.loads(raw);audit=json.loads(a.review.read_bytes())
if audit['status']!='verified_prefix' or audit['contract_sha256']!=b.sha(raw):raise ValueError('predecessor audit mismatch')
for filename,key in [('ledger.jsonl','ledger_sha256'),('costs.jsonl','costs_sha256')]:
 if b.sha((a.prior_run/filename).read_bytes())!=audit[key]:raise ValueError('audited prefix changed')
anchor=json.loads((a.prior_run/'ledger.jsonl').read_text().splitlines()[-1])
if anchor['sha256']!=audit['ledger_head']:raise ValueError('accepted head mismatch')
for name,h in c['code_sha256'].items():
 if b.sha((CORE/name).read_bytes())!=h:raise ValueError('prior source code drift')
proof=verify.verify(a.inputs,a.report,allow_failed=False,node_path=a.node)
if proof['qualified']!=163 or proof['failed_ids']:raise ValueError('compact cohort not fully qualified')
texts={k:Path(r['path']).read_text() for k,r in c['source_rows'].items()}
for k,t in texts.items():
 if b.sha(t.encode())!=c['source_rows'][k]['sha256']:raise ValueError('prior source bytes changed')
accelerator.configure(c['kernel_binary_sha256'],Path(c['kernel_path']));search.joint.compact.Graph=accelerator.TrieGraph
kw=dict(capacity=c['branch_capacity'],record=lambda e:None,initial=anchor['learned_literals'],audited_helpers=c['audited_helpers'])
old=search.Builder(texts,c['owners'],c['references'],c['families'],**kw).score(sorted(c['references']),anchor['learned_literals'])
if old['metrics']!=anchor['metrics'] or old['choices']!=anchor['source_choices']:raise ValueError('anchor remeasurement differs')
added=[]
for pid in proof['eligible_ids']:
 owner=str(pid);path=a.report.parent/f'{pid}.js';source=path.read_text();h=b.sha(source.encode())
 if owner not in c['references']:raise ValueError('new source outside fit300')
 if any(c['owners'][k]==owner and r['sha256']==h for k,r in c['source_rows'].items()):continue
 key=owner+':compact-direct-'+h;c['owners'][key]=owner;c['source_rows'][key]={'label':'compact-direct-'+h,'path':str(path),'sha256':h,'bytes':len(source.encode()),'qualification_report_sha256':proof['report_sha256'],'all_helpers_and_adapters_in_complete_source':True};texts[key]=source;added.append(pid)
new=search.Builder(texts,c['owners'],c['references'],c['families'],**kw).score(sorted(c['references']),anchor['learned_literals'])
# Source addition can change choices, never dictionary or population.
if new['metrics']['selections']>old['metrics']['selections'] or new['learned']!=old['learned']:raise ValueError('source-only invariant failure')
measured,_=search.joint.compare.measure({p:texts[k] for p,k in new['choices'].items()},search.ALPHABET+new['learned'],7 if c['branch_capacity']==128 else 8)
if measured['selections']!=new['metrics']['selections'] or measured['single_character_bits']//(7 if c['branch_capacity']==128 else 8)!=new['metrics']['characters']:raise ValueError('independent source-only costs differ')
pins=dict(c['code_sha256']);paths=[HERE/'prepare.py',HERE/'CONTRACT.md']+[LIT/n for n in verify.replay.supply.pins()]
for path in paths:pins[os.path.relpath(path,CORE)]=b.sha(path.read_bytes())
c.update(schema='gamma.incremental-qualified-compact-supply.v6',code_sha256=pins,initial_learned=anchor['learned_literals'],initial_frontier=[],predecessor_contract_sha256=b.sha(raw),predecessor_ledger_head=anchor['sha256'],predecessor_review_sha256=b.sha(a.review.read_bytes()),source_supply_report_sha256=proof['report_sha256'],source_additions=added,policy_successor='same optimizer and vocabulary; add freshly qualified compact structural alternatives')
summary={'source_additions':len(added),'source_variants':len(texts),'changed_source_problems':[p for p in old['choices'] if old['choices'][p]!=new['choices'][p]],'before':old['metrics'],'after':new['metrics'],'protected_access':False,'m1_qualified':False,'fit_population':300,'m1_population':500,'dictionary_unchanged':True,'qualification_report_sha256':proof['report_sha256']}
a.output.mkdir(parents=True,exist_ok=False);b.write(a.output/'contract.json',c);b.write(a.output/'source-only-summary.json',summary);print(json.dumps(summary))
