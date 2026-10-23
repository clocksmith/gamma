"""Pin fixed-source/qualification/runtime identities; no corpus analysis."""
import hashlib
import json
from pathlib import Path
import platform
import sys
import numpy,scipy
import scipy.optimize._highspy._core as highs
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((LIT/'lns-naming-v1/contract.json').read_text())
c={k:old[k] for k in ('partition','decoder_dependency_bytes','runtime_files','code_hashes')}
c.update(schema='gamma.character-slots.contract.v1',python_bin='/home/x/deco/gamma/.venv_rocm/bin/python',
    versions={'python':platform.python_version(),'numpy':numpy.__version__,'scipy':scipy.__version__},
    seed_relative_path='binding-descent/run-v1/scope_joint-256',private_files={},
    search={'moves':12,'seconds':1800,'solver_seconds':120,'max_length':64,'free_total':48,'free_characters':8,'priority_characters':4,'top':3000,'random':1000,'seed':24},
    cores=[[0,1,2,3],[4,5,6,7]],limits={'workers':2,'address_space_bytes':8589934592,'overall_seconds':2400},
    pre_freeze_audit={'corpus_character_or_cost_probe':False,'tests':4,'exhaustive_instances':40})
work=Path('/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1')
for file in ('dictionary.json','fit-sources.json','sources.json'):
    rel=c['seed_relative_path']+'/'+file;c['private_files'][rel]=sha(work/rel)
for file in ('repair.py','run.py','test_repair.py','make_contract.py','FREEZE.md'):
    c['code_hashes'][str((HERE/file).relative_to(LIT))]=sha(HERE/file)
for rel in ('lns-naming-v1/evidence/results.json','binding-descent-v1/evidence/results.json'):
    c['code_hashes'][rel]=sha(LIT/rel)
c['qualification_evidence_sha256']=sha(LIT/'lns-naming-v1/evidence/results.json')
c['offline_encoder_files']={str((LIT/rel).resolve()):h for rel,h in c['code_hashes'].items() if rel.endswith(('.py','.cjs')) and '/test_' not in rel}
c['offline_encoder_files'].update({p:h for p,h in c['runtime_files'].items() if p.endswith(('.js','.cjs'))})
c['offline_encoder_bytes']=sum(Path(p).stat().st_size for p in c['offline_encoder_files'])
c['offline_encoder_scope']='Conservative inherited source/parser inventory; pinned solver/Python binaries are not a complete measured runtime installation.'
(HERE/'contract.json').write_text(json.dumps(c,sort_keys=True,indent=2)+'\n')
