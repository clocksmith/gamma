"""Inherit public input identities; never open private source/q/result files."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
if not __debug__ or sys.flags.optimize or 'PYTHONOPTIMIZE' in os.environ:raise RuntimeError('assertions required')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent_path=LIT/'all-substring-fraction-v1/contract.json';parent=json.loads(parent_path.read_text())
evidence_path=LIT/'all-substring-fraction-v1/evidence/results.json';evidence=json.loads(evidence_path.read_text())
assert evidence['complete'] and not evidence['validation_loaded'] and evidence['contract_sha256']==sha(parent_path)
c=copy.deepcopy(parent)
c.update(schema='gamma.length-sensitive-fraction.contract.v1',parent_recorded_commit='c8ed60959',
         parent_contract_sha256=sha(parent_path),parent_evidence='all-substring-fraction-v1/evidence/results.json',
         parent_private_results='all-substring-fraction/run-v1/results.json',parent_q={},
         length_bins=[[1,1],[2,2],[3,3],[4,4],[5,8],[9,16],[17,32],[33,64],[65,128],[129,256],[257,None]],
         adaptive_start={'parent_bounds':{a['cohort']:a['optimization']['certificate']['integer_lower_bound'] for a in evidence['arms']},
                         'parent_reported_retained_q':'all_zero; actual private q remains unopened until execution',
                         'known_parent_generated_infeasible':sum(a['optimization']['primal_infeasible'] for a in evidence['arms'])},
         pre_freeze_audit={'private_source_q_or_results_opened':False,'synthetic_only':True})
c['search'].update(multiplier_family='nonnegative source/start/length-bin q',initialization='independently verified item33 lift',
    bin_release_order='bin0..10; half_floor then zero, from initial q; exact identity dedup; never repair',
    iterations=2000,seconds=1200,halve_after=30,primal_every=25,denominator=1000000)
c['limits']={'workers':2,'arm_cores':{'R':[14],'naming':[15]},'address_space_bytes':8*1024**3,'overall_seconds':2400}
c['private_files'][c['parent_private_results']]=evidence['private_results_sha256']
for a in evidence['arms']:
    rel=f"all-substring-fraction/run-v1/{a['cohort']}-flex256/certificate-q.json"
    c['parent_q'][a['cohort']]=rel;c['private_files'][rel]=a['optimization']['certificate']['q_sha256']
for rel in ('all-substring-fraction-v1/contract.json','all-substring-fraction-v1/evidence/results.json','all-substring-fraction-v1/report.py'):
    c['code_hashes'][rel]=sha(LIT/rel)
for p in HERE.iterdir():
    if p.suffix=='.py' or p.name in ('DRAFT.md','FREEZE.md'):c['code_hashes'][str(p.relative_to(LIT))]=sha(p)
c['decoder_source_files']={}
for rel in ('literals.py','pass2/working/bitpack.py'):
    p=LIT/rel;assert p.is_file();c['decoder_source_files'][rel]={'sha256':sha(p),'bytes':p.stat().st_size}
assert c['decoder_dependency_bytes']==sum(r['bytes'] for r in c['decoder_source_files'].values())>0
c['offline_encoder_files']={str((LIT/rel).resolve()):h for rel,h in c['code_hashes'].items() if rel.endswith(('.py','.cjs')) and '/test_' not in rel}
c['offline_encoder_files'].update({p:h for p,h in c['runtime_files'].items() if p.endswith(('.js','.cjs'))})
c['offline_encoder_bytes']=sum(Path(p).stat().st_size for p in c['offline_encoder_files'])
(HERE/'contract.json').write_text(json.dumps(c,sort_keys=True,indent=2)+'\n')
print(json.dumps({'contract_sha256':sha(HERE/'contract.json'),'private_inputs_opened':False,'pinned_fit_ids':len(c['fit_ids'])}))
